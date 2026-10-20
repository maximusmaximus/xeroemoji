"""The sheet label must come from the same record as its images (regression for the v5 misaligned labels)."""
import os,sys,json,tempfile
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
from PIL import Image
from diffcheck import sheet
import pytest
def _png(d,code,c):
    p=os.path.join(d,code+'.png'); Image.new('RGBA',(32,32),c).save(p); return p
def test_labels_match_images():
    d=tempfile.mkdtemp(); recs=[dict(code=c,label=f'name {c}',images=[('a',_png(d,c,(i*20,0,0,255)))]) for i,c in enumerate(['1f4a2','1f577','1f578','1f4ce','1f587'])]
    lay=sheet(recs,os.path.join(d,'s.png'),64,2)
    for r,l in zip(recs,lay):
        assert l['code']==r['code']; assert all(os.path.basename(p).split('.')[0]==l['code'] for p in l['images'])
        x0,y0,x1,y1=l['cell']; lx,ly=l['label_xy']; assert x0<=lx<x1 and y0<=ly<y1   # label sits inside its own cell, above its images
def test_mismatched_record_rejected():
    d=tempfile.mkdtemp(); p=_png(d,'1f577',(0,0,0,255))
    with pytest.raises(AssertionError): sheet([dict(code='1f4a2',label='anger',images=[('a',p)])],os.path.join(d,'s.png'),64,1)
