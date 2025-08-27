# decoder4b.py - UE4T reference decoder (v0.1)
from typing import List, Tuple

TOK = {
    "SILENT": 0x0,
    "SDP":    0x1,
    "SDM":    0x2,
    "SCALEP": 0x3,
    "SCALEM": 0x4,
    "MAX":    0x5,
    "MIN":    0x6,
    "BASE":   0x7,
    "NORM":   0x8,
    "RLE":    0x9,
    "RESET":  0xA,
    "KEEP":   0xB,
    "CRC":    0xC,
}

def iter_tokens(stream: List[Tuple[float,int]]):
    for (t,n) in stream:
        yield (t, n & 0xF)

class UE4TDecoder:
    def __init__(self, beta=0.05, lambda0=0.25, T_emit=5.0, E0=0, sdK=1.0):
        self.beta = beta
        self.lambda0 = lambda0
        self.T_emit = T_emit
        self.E = E0
        self.sdK = sdK
        self.reset()

    def reset(self, b0=20.0):
        self.b = b0
        self.r = 0.0
        self.last_t = -1e9
        self.expect_norm_payload = False

    def dequant_norm(self, payload: int):
        sgn = -1.0 if (payload>>3)&1 else 1.0
        m = payload & 0x7
        mant = 1.0 + m/8.0
        return sgn * mant

    def apply(self, t: float, nib: int, xhat: List[Tuple[float,float]]):
        E = self.E
        scale = (1<<E)
        if self.expect_norm_payload:
            delta = self.dequant_norm(nib) * scale
            if len(xhat)==0:
                cur = self.b + delta
            else:
                cur = xhat[-1][1] + delta
            xhat.append((t, cur))
            self.expect_norm_payload = False
            return

        if nib == TOK["NORM"]:
            self.expect_norm_payload = True
        elif nib == TOK["SDP"]:
            step = (self.lambda0*scale)*self.sdK
            cur = (xhat[-1][1] if xhat else self.b) + step
            xhat.append((t, cur))
        elif nib == TOK["SDM"]:
            step = (self.lambda0*scale)*self.sdK
            cur = (xhat[-1][1] if xhat else self.b) - step
            xhat.append((t, cur))
        elif nib == TOK["MAX"]:
            cur = (xhat[-1][1] if xhat else self.b) + (4.0*scale)  # conceptual big jump
            xhat.append((t, cur))
        elif nib == TOK["MIN"]:
            cur = (xhat[-1][1] if xhat else self.b) - (4.0*scale)
            xhat.append((t, cur))
        elif nib == TOK["SCALEP"]:
            self.E += 1
        elif nib == TOK["SCALEM"]:
            self.E = max(0, self.E-1)
        elif nib == TOK["SILENT"]:
            if len(xhat)==0:
                xhat.append((t, self.b))
            else:
                xhat.append((t, xhat[-1][1]))

    def decode(self, stream: List[Tuple[float,int]]):
        xhat = []
        for (t,n) in iter_tokens(stream):
            self.apply(t, n, xhat)
        return xhat
