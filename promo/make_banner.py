from PIL import Image,ImageDraw,ImageFont
import os,random
random.seed(7)
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','png');files=sorted(f for f in os.listdir(P) if '-' not in f and f.startswith('1f'))
random.shuffle(files)
OS='/usr/share/fonts/truetype/sand-box/google/Oswald/Oswald-VariableFont_wght.ttf'
MO='/usr/share/fonts/truetype/sand-box/google/Montserrat/Montserrat-VariableFont_wght.ttf'
def font(p,s,w):
    f=ImageFont.truetype(p,s)
    try:f.set_variation_by_axes([w])
    except Exception:pass
    return f
cache={}
def em(i,s):
    k=(i,s)
    if k not in cache:cache[k]=Image.open(os.path.join(P,files[i%len(files)])).convert('RGBA').resize((s,s),Image.LANCZOS)
    return cache[k]
def make(W,H,out):
    im=Image.new('RGB',(W,H),(14,14,28));d=ImageDraw.Draw(im)
    cell=90;s=78;cols=(W-40)//cell;rows=(H-40)//cell
    ox=(W-cols*cell)//2;oy=(H-rows*cell)//2
    # center panel in cells
    pc0,pc1=2,cols-3; pr0=rows//2-3 if H>W else rows//2-3; pr1=pr0+6
    n=0
    for r in range(rows):
        for c in range(cols):
            if pc0<=c<=pc1 and pr0<=r<=pr1:continue
            im.paste(em(n,s),(ox+c*cell+(cell-s)//2,oy+r*cell+(cell-s)//2),em(n,s));n+=1
    x0,y0=ox+pc0*cell+8,oy+pr0*cell+8;x1,y1=ox+(pc1+1)*cell-8,oy+(pr1+1)*cell-8
    d.rounded_rectangle((x0,y0,x1,y1),30,fill=(255,214,10))
    cx=W//2;pw=x1-x0-60
    def fit(txt,p,size,w):
        while True:
            f=font(p,size,w)
            if d.textlength(txt,font=f)<=pw:return f
            size-=2
    ft=fit('XERO EMOJI',OS,170,700);fw=fit('WORLD',OS,170,700)
    fs=fit('3,963 emoji · one 3D world',MO,44,700);fu=fit('xeroemoji.grok.me',MO,52,800)
    lines=[('XERO EMOJI',ft,(14,14,28)),('WORLD',fw,(14,14,28)),('3,963 emoji · one 3D world',fs,(40,40,60)),('xeroemoji.grok.me',fu,(200,30,90))]
    hs=[d.textbbox((0,0),t,font=f) for t,f,_ in lines];gap=18
    tot=sum(b[3]-b[1] for b in hs)+gap*3;y=(y0+y1)//2-tot//2
    for (t,f,col),b in zip(lines,hs):
        d.text((cx,y-b[1]),t,font=f,fill=col,anchor='la' if False else None) if False else d.text((cx-(b[2]-b[0])//2-b[0],y-b[1]),t,font=f,fill=col)
        y+=b[3]-b[1]+gap
    im.save(out,optimize=True);print(out,n)
make(1080,1350,os.path.dirname(os.path.abspath(__file__))+'/instagram-xero-world-banner.png')
make(1080,1080,os.path.dirname(os.path.abspath(__file__))+'/instagram-xero-world-banner-square.png')
