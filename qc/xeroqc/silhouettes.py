"""Reference silhouettes for group-shape rules (keycaps, country flags, symbol tiles): the per-pixel majority vote of the
alpha masks (128px) of every member of the class. Deterministic (sorted inputs)."""
import numpy as np
from PIL import Image
from .paths import SET
N=128
def mask(f,path=None):
    a=np.asarray(Image.open(path or f'{SET}/png/{f}.png').convert('RGBA').resize((N,N),Image.BILINEAR))[...,3]
    return a>128
def bleed(m):
    """full-bleed art: the alpha bounding box spans >=94% of the canvas both ways (tiles, round signs, badges)"""
    ys,xs=np.nonzero(m)
    return bool(len(xs)) and (xs.max()-xs.min()+1)>=.94*N and (ys.max()-ys.min()+1)>=.94*N
def is_tile(m):
    """a tile = the art fills (>=88%) a bounding box that spans >=94% of the canvas both ways (keycap/button tiles)"""
    ys,xs=np.nonzero(m)
    if not len(xs): return False
    w=xs.max()-xs.min()+1; h=ys.max()-ys.min()+1
    return w>=.94*N and h>=.94*N and m.sum()/(w*h)>=.88
def classes(ctx,files):
    C={'keycap':[],'flag':[],'tile':[]}
    for f in files:
        k,r=ctx.row(f)
        if not r: continue
        if r['subgroup']=='keycap': C['keycap'].append(f)
        elif r['subgroup'] in ('country-flag','subdivision-flag'): C['flag'].append(f)
        elif r['group']=='Symbols' and is_tile(mask(f)): C['tile'].append(f)
    return C
def build(ctx,files):
    C=classes(ctx,sorted(files)); ref={}
    for k,fl in C.items():
        if fl: ref[k]=(np.mean([mask(f) for f in fl],0)>=.5)
    return C,ref
def iou(a,b):
    u=(a|b).sum(); return float((a&b).sum()/u) if u else 1.0
