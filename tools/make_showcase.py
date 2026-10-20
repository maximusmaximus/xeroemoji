#!/usr/bin/env python3
"""Render the README showcase images into docs/images/ from the approved png/ files (art is only read, never changed).
Needs Pillow. Usage: python3 tools/make_showcase.py [--font PATH_TO_BOLD_TTF]"""
import json,os,re,sys,random
from PIL import Image,ImageDraw,ImageFont
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=R+'/docs/images'; os.makedirs(OUT,exist_ok=True)
M=json.load(open(R+'/demos/emoji-map.json',encoding='utf-8'))
fa=sys.argv[sys.argv.index('--font')+1] if '--font' in sys.argv else None
def font(sz,bold=True):
    for p in [fa,'/usr/share/fonts/truetype/sand-box/google/Poppins/Poppins-'+('Bold' if bold else 'Regular')+'.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf']:
        if p and os.path.exists(p): return ImageFont.truetype(p,sz)
    return ImageFont.load_default()
_c={}
def em(f,n):
    if (f,n) not in _c: _c[f,n]=Image.open(f'{R}/png/{f}.png').convert('RGBA').resize((n,n),Image.LANCZOS)
    return _c[f,n]
TONE=re.compile(r'-1f3f[b-f]')
def base(g): return [v for k,v in M.items() if v[3]==g and not TONE.search(k)]
BG=(251,250,247)

def hero():
    W,H=1600,560; im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    picks=['1f600','1f60d','1f923','1f92f','1f60e','1f973','1f47d','1f4a9','1f431','1f436','1f984','1f419','1f355','1f354','1f369','1f680',
           '1f308','1f525','2764','1f3b8','1f3ae','26bd','1f381','1f4a1','1f9d1-1f3fd-200d-1f680','1f469-1f3ff-200d-1f373','1f44d-1f3fe','1f44b-1f3fb',
           '1f9d9','1f9dc-200d-2640','1f1ef-1f1f5','1f3f3-200d-1f308','1f30d','1f335','1f98b','1f388','1f9c1','1f6f8','1f47b','1f921']
    random.seed(7); spots=[]
    for i,f in enumerate(picks):
        for _ in range(400):
            n=random.choice([96,112,128,150]); x=random.randint(-30,W-n+30); y=random.randint(-30,H-n+30)
            if 430<x+n/2<1170 and 130<y+n/2<430: continue          # keep the title area clear
            if all((x-a)**2+(y-b)**2>((n+m)/2*0.92)**2 for a,b,m in spots): break
        spots.append((x,y,n)); t=em(f,n).rotate(random.uniform(-12,12),Image.BICUBIC,expand=True); im.paste(t,(x,y),t)
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov); od.rounded_rectangle((470,150,1130,410),radius=36,fill=(255,255,255,235)); im.paste(ov,(0,0),ov)
    d=ImageDraw.Draw(im); f1=font(104); f2=font(30,False)
    for txt,fn,y,col in [('Xero Emoji',f1,170,(29,27,24)),('3,963 emoji · Unicode Emoji 18.0 · SVG + PNG',f2,312,(90,84,76)),('started in 2016 · by Max Infeld',f2,352,(160,23,159))]:
        w=d.textlength(txt,font=fn); d.text(((W-w)/2,y),txt,font=fn,fill=col)
    im.save(OUT+'/hero.jpg',quality=86,optimize=True); return 'hero.jpg'

def sheet(title,items,fname,cell=56,cols=20,pad=24):
    rows=(len(items)+cols-1)//cols; W=pad*2+cols*cell; H=pad*2+70+rows*cell
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((pad,pad-4),title,font=font(30),fill=(29,27,24)); d.text((pad,pad+38),f'{len(items)} emoji · Xero Emoji',font=font(17,False),fill=(107,102,94))
    for i,v in enumerate(items):
        t=em(v[0],cell-8); im.paste(t,(pad+(i%cols)*cell+4,pad+70+(i//cols)*cell+4),t)
    im.save(f'{OUT}/{fname}',quality=84,optimize=True); return fname

def tones():
    T=['','1f3fb','1f3fc','1f3fd','1f3fe','1f3ff']
    ks=['1f44b','1f44d','1f64f','1f4aa','1f9d1','1f476','1f9d1-200d-1f373','1f469-200d-1f680','1f9d1-200d-1f3a8','1f9d9','1f3c4','1f6b4']
    cell=88; pad=24; W=pad*2+len(T)*cell+300; H=pad*2+70+len(ks)*cell
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((pad,pad-4),'Skin tones',font=font(30),fill=(29,27,24)); d.text((pad,pad+38),'default + 5 Fitzpatrick modifiers on every emoji that supports them',font=font(17,False),fill=(107,102,94))
    for r,k in enumerate(ks):
        for c,t in enumerate(T):
            kk=k if not t else (lambda p:'-'.join(p[:1]+[t]+p[1:]))(k.split('-'))
            if kk not in M: continue
            e=em(M[kk][0],cell-10); im.paste(e,(pad+c*cell+5,pad+70+r*cell+5),e)
        d.text((pad+len(T)*cell+16,pad+70+r*cell+cell/2-12),M[k][2],font=font(19,False),fill=(60,56,50))
    im.save(OUT+'/skin-tones.jpg',quality=84,optimize=True); return 'skin-tones.jpg'

out=[hero(),tones()]
for g,fn in [('Smileys & Emotion','smileys.jpg'),('People & Body','people.jpg'),('Animals & Nature','animals.jpg'),('Food & Drink','food.jpg'),
             ('Travel & Places','travel.jpg'),('Activities','activities.jpg'),('Objects','objects.jpg'),('Symbols','symbols.jpg'),('Flags','flags.jpg')]:
    out.append(sheet(g+(' (default tone)' if g=='People & Body' else ''),base(g),fn))
for f in out: print(f, os.path.getsize(f'{OUT}/{f}')//1024,'KB')
