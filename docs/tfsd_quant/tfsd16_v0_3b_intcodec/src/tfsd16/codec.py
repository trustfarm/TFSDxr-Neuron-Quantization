## License
## Apache License 2.0 © 2025 TrustFarm  
## SPDX-License-Identifier: Apache-2.0

# TFSD16_V0_3b codec (Python)
# - Fixed Sign/Exponent (SE) path (keep 6 bits as-is; SE change -> KF for simplicity/quality)
# - Mantissa path: M5+1 absolute patching per window (5 bits + 1 bridge bit) with up to W patches per sample
# - ZeroRun type=11 (nibble-aligned): pad->0xF marker->runlen(4b)
# - KF type=00 (16b payload)
# - Patch type=01: pc(2b)=count-1, then per-patch [shift2(+pos3), payload]
# - Closed-loop: always compare vs decoder's previous (prev = FP16_dec(t-1))
# - Delta_t definition is inherent: Delta_t = FP_e(t) - FP_d(t-1) in FP16 field space
# - Optional RD-switch encoder: min(bits(KF), bits(M5+1 patch frame))

from __future__ import annotations
import numpy as np

# -------- Bit I/O --------
class BW:
    def __init__(self): self.buf=bytearray(); self.acc=0; self.n=0; self.bits=0
    def put(self,v,k):
        v&=(1<<k)-1; self.acc=(self.acc<<k)|v; self.n+=k; self.bits+=k
        while self.n>=8:
            self.n-=8; self.buf.append((self.acc>>self.n)&0xFF); self.acc&=(1<<self.n)-1
    def pad_to_nibble(self):
        pad=(4-(self.bits%4))%4
        if pad: self.put(0,pad)
    def finish(self):
        if self.n>0: self.buf.append((self.acc<<(8-self.n))&0xFF); self.acc=0; self.n=0
        return bytes(self.buf)

class BR:
    def __init__(self,b): self.b=b; self.i=0; self.acc=0; self.n=0; self.bits=0
    def get(self,k):
        while self.n<k:
            if self.i>=len(self.b): raise EOFError("bitstream exhausted")
            self.acc=(self.acc<<8)|self.b[self.i]; self.i+=1; self.n+=8
        self.n-=k; v=(self.acc>>self.n)&((1<<k)-1); self.acc&=(1<<self.n)-1; self.bits+=k; return v
    def bits_left(self): return len(self.b)*8 - self.bits
    def pad_to_nibble(self):
        pad=(4-(self.bits%4))%4
        if pad: _=self.get(pad)

# -------- FP16 helpers --------
def f32_to_fp16_bits(x): return x.astype(np.float16).view(np.uint16)
def fp16_bits_to_f32(h): return h.view(np.float16).astype(np.float32)
def split_fields(hv:int): return (hv>>15)&1, (hv>>10)&0x1F, hv&0x3FF
def join_fields(S:int,E:int,M:int)->int: return ((S&1)<<15)|((E&0x1F)<<10)|(M&0x3FF)

def choose_pos_for_hb(Mt, Mp):
    diff=Mt^Mp
    if diff==0: return None
    hb=diff.bit_length()-1
    pos=max(0, min(7, 9-hb)); msb=9-pos
    return pos, msb, hb

# -------- Decoder (generic patch parser, payload bits selectable) --------
def decode_generic(b,N, payload_bits_per_patch:int):
    br=BR(b); out=np.zeros(N,dtype=np.uint16)
    try:
        if br.get(2)!=0b00: return out, {"error":"no KF0", "t_end":0, "bits_used":br.bits}
        out[0]=np.uint16(br.get(16))
    except EOFError:
        return out, {"error":"eof KF0", "t_end":0, "bits_used":getattr(br,'bits',None)}
    prev=int(out[0]); prev_pos=0; t=1; info={"error":None}
    while t<N:
        if br.bits_left()<2: out[t:]=np.uint16(prev); break
        try: typ=br.get(2)
        except EOFError: out[t:]=np.uint16(prev); info["error"]="eof type"; break
        if typ==0b00:  # KF
            if br.bits_left()<16: out[t:]=np.uint16(prev); info["error"]="padding before KF"; break
            try: out[t]=np.uint16(br.get(16))
            except EOFError: out[t:]=np.uint16(prev); info["error"]="eof KF"; break
            prev=int(out[t]); prev_pos=0; t+=1; continue
        if typ==0b11:  # ZeroRun
            pad=(4-(br.bits%4))%4
            if br.bits_left()<pad+8: out[t:]=np.uint16(prev); info["error"]="padding before ZR"; break
            br.pad_to_nibble()
            try: marker=br.get(4); run=br.get(4)
            except EOFError: out[t:]=np.uint16(prev); info["error"]="eof ZR"; break
            if marker!=0xF: out[t:]=np.uint16(prev); info["error"]="bad ZR"; break
            end=min(N, t+max(0,min(15,int(run)))); out[t:end]=np.uint16(prev); t=end; continue
        if typ==0b01:  # Patch
            if br.bits_left()<2: out[t:]=np.uint16(prev); info["error"]="padding before pc"; break
            try: pc=br.get(2)+1
            except EOFError: out[t:]=np.uint16(prev); info["error"]="eof pc"; break
            S,E,Md=split_fields(prev); cur_pos=prev_pos; cur_M=Md
            ok=True
            for _ in range(pc):
                if br.bits_left()<2: ok=False; break
                try: sh=br.get(2)
                except EOFError: ok=False; break
                if   sh==0: pos=cur_pos
                elif sh==1: pos=max(0,cur_pos-1)
                elif sh==2: pos=min(7,cur_pos+1)
                else:
                    if br.bits_left()<3: ok=False; break
                    try: pos=br.get(3)
                    except EOFError: ok=False; break
                cur_pos=pos; msb=9-pos
                if br.bits_left()<payload_bits_per_patch: ok=False; break
                try: payload=br.get(payload_bits_per_patch)
                except EOFError: ok=False; break
                if payload_bits_per_patch==6:  # M5+1
                    m5=(payload>>1)&0b11111; b1=payload&1
                    # write [msb..msb-4]
                    for i in range(5):
                        idx=msb-i; bit=(m5>>(4-i))&1
                        if 0<=idx<=9:
                            if bit: cur_M|=(1<<idx)
                            else:   cur_M&=~(1<<idx)
                    if msb-5>=0:
                        if b1: cur_M|=(1<<(msb-5))
                        else:  cur_M&=~(1<<(msb-5))
                elif payload_bits_per_patch==3:  # val3
                    v3=payload & 0b111
                    mask=((1<<3)-1)<<(msb-2)
                    cur_M=(cur_M & ~mask) | (v3<<(msb-2))
                else:
                    ok=False; break
            if not ok:
                out[t:]=np.uint16(prev); info["error"]="patch parse"; break
            prev=join_fields(S,E,cur_M); prev_pos=cur_pos; out[t]=np.uint16(prev); t+=1; continue
        # unknown
        out[t:]=np.uint16(prev); info["error"]="bad type"; break
    info["t_end"]=t; info["bits_used"]=br.bits
    return out, info

# -------- Encoders --------
def encode_m5p1(x_f32, kf_period=22050, W=2, l6_watch=2205, l6_accum_thresh=64, eps=1e-3):
    h=f32_to_fp16_bits(x_f32)
    bw=BW(); bw.put(0b00,2); bw.put(int(h[0]),16)
    prev=int(h[0]); prev_pos=0; l6_age=0; l6_accum=0; t=1
    while t<len(h):
        # ZeroRun
        zr=0
        while t<len(h) and int(h[t])==prev and zr<15:
            zr+=1; t+=1
        if zr>0:
            bw.put(0b11,2); bw.pad_to_nibble(); bw.put(0xF,4); bw.put(zr,4); continue
        if t>=len(h): break
        # KF periodic
        if kf_period and (t%kf_period==0):
            bw.put(0b00,2); bw.put(int(h[t]),16)
            prev=int(h[t]); prev_pos=0; l6_age=0; l6_accum=0; t+=1; continue
        S,E,M=split_fields(int(h[t])); Sd,Ed,Md=split_fields(prev)
        # SE change -> KF
        if (S!=Sd) or (E!=Ed):
            bw.put(0b00,2); bw.put(int(h[t]),16)
            prev=int(h[t]); prev_pos=0; l6_age=0; l6_accum=0; t+=1; continue
        # up to W patches
        patches=[]; cur_M=Md; cur_pos=prev_pos; touched_l6=False
        for _ in range(max(1,W)):
            sel=choose_pos_for_hb(M, cur_M)
            if sel is None: break
            pos, msb, hb = sel
            delta=pos-cur_pos
            if delta==0: shift2, pos3 = 0, None
            elif delta==-1: shift2, pos3 = 1, None; cur_pos=pos
            elif delta==1:  shift2, pos3 = 2, None; cur_pos=pos
            else:           shift2, pos3 = 3, pos&0b111; cur_pos=pos
            # payload 6b
            m5=0
            for i in range(5):
                idx=msb-i; bit=(M>>idx)&1 if 0<=idx<=9 else 0
                m5=(m5<<1)|bit
            b1=(M>>(msb-5))&1 if (msb-5)>=0 else 0
            payload=(m5<<1)|b1
            patches.append((shift2,pos3,payload,msb))
            # apply to current
            for i in range(5):
                idx=msb-i; bit=(m5>>(4-i))&1
                if 0<=idx<=9:
                    if bit: cur_M|=(1<<idx)
                    else:   cur_M&=~(1<<idx)
            if (msb-5)>=0:
                if b1: cur_M|=(1<<(msb-5))
                else:  cur_M&=~(1<<(msb-5))
            if msb<=5: touched_l6=True
            # epsilon guard
            y = fp16_bits_to_f32(np.array([join_fields(Sd,Ed,cur_M)],dtype=np.uint16))[0]
            yt=fp16_bits_to_f32(np.array([int(h[t])],dtype=np.uint16))[0]
            if abs(y-yt)<=eps: break
        # l6 accum/watch
        if not touched_l6: l6_accum += abs((M&0x3F)-(Md&0x3F))
        else: l6_accum = 0
        if l6_age>=l6_watch or l6_accum>=l6_accum_thresh:
            bw.put(0b00,2); bw.put(int(h[t]),16)
            prev=int(h[t]); prev_pos=0; l6_age=0; l6_accum=0; t+=1; continue
        # emit patch
        count=max(1, min(4, len(patches)))
        bw.put(0b01,2); bw.put(count-1,2)
        cur_pos_w=prev_pos; Md_w=Md
        for i in range(count):
            shift2,pos3,payload,msb=patches[i]
            if pos3 is None: bw.put(shift2,2)
            else: bw.put(3,2); bw.put((9-msb)&0b111,3)
            bw.put(payload,6)
            if shift2==1: cur_pos_w-=1
            elif shift2==2: cur_pos_w+=1
            elif shift2==3: cur_pos_w=(9-msb)
            # apply to Md_w
            m5=(payload>>1)&0b11111; b1=payload&1
            for j in range(5):
                idx=msb-j; bit=(m5>>(4-j))&1
                if 0<=idx<=9:
                    if bit: Md_w|=(1<<idx)
                    else:   Md_w&=~(1<<idx)
            if (msb-5)>=0:
                if b1: Md_w|=(1<<(msb-5))
                else:  Md_w&=~(1<<(msb-5))
        prev=join_fields(Sd,Ed,Md_w); prev_pos=cur_pos; l6_age = 0 if touched_l6 else (l6_age+1); t+=1
    return bw.finish(), bw.bits

def decode_m5p1(b,N):
    return decode_generic(b,N, payload_bits_per_patch=6)

# -------- Optional RD-switch (min bits among {KF, M5+1}) --------
def encode_m5p1_rd(x_f32, kf_period=22050, W=2):
    h=f32_to_fp16_bits(x_f32)
    bw=BW(); bw.put(0b00,2); bw.put(int(h[0]),16)
    prev=int(h[0]); prev_pos=0; t=1
    while t<len(h):
        # ZeroRun
        zr=0
        while t<len(h) and int(h[t])==prev and zr<15:
            zr+=1; t+=1
        if zr>0:
            bw.put(0b11,2); bw.pad_to_nibble(); bw.put(0xF,4); bw.put(zr,4); continue
        if t>=len(h): break
        if kf_period and (t%kf_period==0):
            bw.put(0b00,2); bw.put(int(h[t]),16)
            prev=int(h[t]); prev_pos=0; t+=1; continue
        S,E,M=split_fields(int(h[t])); Sd,Ed,Md=split_fields(prev)
        if (S!=Sd) or (E!=Ed):
            bw.put(0b00,2); bw.put(int(h[t]),16)
            prev=int(h[t]); prev_pos=0; t+=1; continue
        # candidate patches
        patches=[]; cur_M=Md; cur_pos=prev_pos; cap=W; bits_overhead=2+2
        per_bits=[]
        while cur_M!=M and cap>0:
            pos, msb, _ = choose_pos_for_hb(M, cur_M)
            delta=pos-cur_pos
            if delta==0: shift2, pos3_bits=0,0; bits=2+6
            elif delta==-1: shift2, pos3_bits=1,0; bits=2+6; cur_pos=pos
            elif delta==1:  shift2, pos3_bits=2,0; bits=2+6; cur_pos=pos
            else:           shift2, pos3_bits=3,3; bits=2+6+3; cur_pos=pos
            # payload
            m5=0
            for i in range(5):
                idx=msb-i; bit=(M>>idx)&1 if 0<=idx<=9 else 0
                m5=(m5<<1)|bit
            b1=(M>>(msb-5))&1 if (msb-5)>=0 else 0
            payload=(m5<<1)|b1
            patches.append((shift2, (9-msb)&0b111 if shift2==3 else None, payload, msb))
            per_bits.append(bits)
            # apply
            for i in range(5):
                idx=msb-i; bit=(m5>>(4-i))&1
                if 0<=idx<=9:
                    if bit: cur_M|=(1<<idx)
                    else:   cur_M&=~(1<<idx)
            if (msb-5)>=0:
                if b1: cur_M|=(1<<(msb-5))
                else:  cur_M&=~(1<<(msb-5))
            cap-=1
        # choose min bits
        patch_bits = bits_overhead + sum(per_bits) if patches else 1e9
        kf_bits = 2+16
        if patches and (cur_M==M) and (patch_bits < kf_bits):
            bw.put(0b01,2); bw.put(len(patches)-1,2)
            for shift2, pos3, payload, msb in patches:
                if pos3 is None: bw.put(shift2,2)
                else: bw.put(3,2); bw.put(pos3,3)
                bw.put(payload,6)
            prev=join_fields(Sd,Ed,cur_M); prev_pos=cur_pos; t+=1; continue
        else:
            bw.put(0b00,2); bw.put(int(h[t]),16)
            prev=int(h[t]); prev_pos=0; t+=1; continue
    return bw.finish(), bw.bits
