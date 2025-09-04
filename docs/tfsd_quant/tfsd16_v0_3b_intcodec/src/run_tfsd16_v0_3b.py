## License
## Apache License 2.0 © 2025 TrustFarm  
## SPDX-License-Identifier: Apache-2.0

# run_tfsd16_v0_3b.py : CLI runner for TFSD16_V0_3b
import os, argparse, numpy as np, pandas as pd
from scipy.io import wavfile
from datetime import datetime
from tfsd16.codec import f32_to_fp16_bits, fp16_bits_to_f32, encode_m5p1, decode_m5p1, encode_m5p1_rd

def snr(a,b): 
    return 10.0*np.log10((np.sum(a*a)+1e-12)/(np.sum((a-b)*(a-b))+1e-12))

def run(files, mode="m5p1", W=2, eps=1e-3, kf_period=22050, l6_watch=2205, l6_accum=64, outdir=None):
    STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
    if outdir is None:
        outdir = os.path.join(os.getcwd(), f"out_{STAMP}")
    os.makedirs(outdir, exist_ok=True)

    rows=[]
    for path in files:
        fs, data = wavfile.read(path)
        x = (data[:,0] if data.ndim>1 else data)
        x = (x.astype(np.float32)/np.iinfo(data.dtype).max) if data.dtype.kind in "iu" else x.astype(np.float32)
        # encode/decode
        if mode=="m5p1":
            bs, bitlen = encode_m5p1(x, kf_period=kf_period, W=W, l6_watch=l6_watch, l6_accum_thresh=l6_accum, eps=eps)
            from tfsd16.codec import decode_m5p1 as dec
        elif mode=="rd":
            bs, bitlen = encode_m5p1_rd(x, kf_period=kf_period, W=W)
            from tfsd16.codec import decode_m5p1 as dec
        else:
            raise ValueError("mode must be m5p1 or rd")

        dec_h, info = dec(bs, len(x))
        y = fp16_bits_to_f32(dec_h)
        # metrics
        fp16_ref = x.astype(np.float16).astype(np.float32)
        row = dict(
            file=os.path.basename(path), fs=int(fs), N=len(x),
            mode=mode, W=W, eps=eps, kf_period=kf_period, l6_watch=l6_watch, l6_accum=l6_accum,
            BPS=bitlen/len(x),
            SNR_FP32=snr(x,y), RMSE_FP32=float(np.sqrt(np.mean((x-y)**2))),
            SNR_FP16ref=snr(fp16_ref,y), RMSE_FP16ref=float(np.sqrt(np.mean((fp16_ref-y)**2))),
            err=info.get("error"), t_end=info.get("t_end")
        )
        rows.append(row)
        # write artifacts
        stem = os.path.splitext(os.path.basename(path))[0]
        with open(os.path.join(outdir, f"{stem}_{mode}_W{W}.bin"), "wb") as f: f.write(bs)
        wavfile.write(os.path.join(outdir, f"{stem}_{mode}_W{W}_dec_{STAMP}.wav"), fs, np.clip(y,-1,1).astype(np.float32))

    df = pd.DataFrame(rows)
    csv = os.path.join(outdir, "metrics.csv")
    df.to_csv(csv, index=False)
    print("Wrote:", outdir)
    return outdir, csv

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="input WAV files")
    ap.add_argument("--mode", choices=["m5p1","rd"], default="m5p1")
    ap.add_argument("--W", type=int, default=2)
    ap.add_argument("--eps", type=float, default=1e-3)
    ap.add_argument("--kf", type=int, default=22050)
    ap.add_argument("--watch", type=int, default=2205)
    ap.add_argument("--accum", type=int, default=64)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    run(args.files, mode=args.mode, W=args.W, eps=args.eps, kf_period=args.kf, l6_watch=args.watch, l6_accum=args.accum, outdir=args.out)
