"""Instagram Story banners (1080x1920) in the style of the Xero Emoji posters (Day City, Carnival, Harbour).
Reuses the approved poster art (/workspace/xeroemoji-book/posters) and the posters' colour-matched border picker."""
import sys,os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
BK='/workspace/xeroemoji-book'; sys.path.insert(0,BK+'/build')
import m_posters as mp
from printlib import mix
R=os.path.dirname(os.path.abspath(__file__))+'/..'; PNG=R+'/png'
W,H=1080,1920; ES=70; STEP=84
EPI=BK+'/build/fonts/Epicenter-Black.ttf'; OS='/usr/share/fonts/truetype/sand-box/google/Montserrat/Montserrat-VariableFont_wght.ttf'
def font(p,s,w=None):
    f=ImageFont.truetype(p,s)
    if w:
        try:f.set_variation_by_axes([w])
        except Exception:pass
    return f
def em(f):
    return Image.open(f'{PNG}/{f}.png').convert('RGBA').resize((ES,ES),Image.LANCZOS)
def make(stem,th,line,out):
    col=th['col']; band=mix(col,(255,255,255),0.72); dark=mix(col,(30,26,72),0.15)
    im=Image.new('RGB',(W,H),band); d=ImageDraw.Draw(im)
    # emoji slots: 3 rows top (0..252), 3 rows bottom, one column each side
    xs=[round(W/2+(k-6)*STEP) for k in range(13)]   # 13 columns centred
    slots=[]
    for r in range(3):
        slots+=[(x,42+r*STEP) for x in xs]; slots+=[(x,H-42-r*STEP) for x in xs]
    side_top,side_bot=42+3*STEP,H-42-3*STEP
    ny=round((side_bot-side_top)/STEP); ys=[side_top+k*(side_bot-side_top)/ny for k in range(ny+1)][0:]
    for y in ys[0:]:
        slots+=[(xs[0],round(y)),(xs[-1],round(y))]
    slots=sorted(set(slots))
    fs=[f for f in mp.hue_pick(col,len(slots)+40,seed=th['seed']) if os.path.exists(f'{PNG}/{f}.png')]
    fs=(fs*3)[:len(slots)]
    # poster art (inside its own border) in the frame window
    P=Image.open(f'{BK}/posters/{stem}/{stem}-print-300ppi.jpg'); PW,PH=P.size; c=440
    art=P.crop((c,c,PW-c,PH-c))
    ha=H-252-8-200-28-260; wa=round(ha*art.width/art.height); x0=W//2-wa//2; x1=x0+wa
    px0=xs[0]+ES//2+18; px1=xs[-1]-ES//2-18
    y0=252+8; art=art.resize((wa,ha),Image.LANCZOS)
    d.rounded_rectangle((x0-12,y0-12,x1+12,y0+ha+12),22,fill=(255,255,255),outline=dark,width=6)
    im.paste(art,(x0,y0))
    # text plate between art and bottom safe line (1670)
    ty0=y0+ha+28; ty1=H-252-8
    d.rounded_rectangle((px0-12,ty0,px1+12,ty1),26,fill=(255,255,255),outline=dark,width=6)
    pw=px1-px0-60
    def fit(t,p,s,w=None):
        while True:
            f=font(p,s,w)
            if d.textlength(t,font=f)<=pw: return f
            s-=2
    f1=fit(line,OS,46,800); f2=fit('xeroemoji.grok.me',OS,72,900)
    b1=d.textbbox((0,0),line,font=f1); b2=d.textbbox((0,0),'xeroemoji.grok.me',font=f2)
    h1,h2=b1[3]-b1[1],b2[3]-b2[1]; g=22; y=(ty0+ty1)//2-(h1+g+h2)//2
    d.text((W//2-(b1[2]-b1[0])//2-b1[0],y-b1[1]),line,font=f1,fill=(30,26,72))
    y+=h1+g; tx=W//2-(b2[2]-b2[0])//2-b2[0]
    d.text((tx,y-b2[1]),'xeroemoji.grok.me',font=f2,fill=mix(col,(30,26,72),0.45))
    for (x,y),f in zip(slots,fs):
        e=em(f); im.paste(e,(x-ES//2,y-ES//2),e)
    im=im.quantize(colors=256,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.FLOYDSTEINBERG) if False else im
    im.save(out,optimize=True)
    if os.path.getsize(out)>1.45e6:
        im.convert('P',palette=Image.ADAPTIVE,colors=256).save(out,optimize=True)
    print(out,os.path.getsize(out),'text',ty0,ty1,'emoji',len(slots))
LINES={'xero-emoji-poster-1-day-city':'Xero Emoji World is live!','xero-emoji-poster-2-carnival':'Step into the Carnival — it\'s live!','xero-emoji-poster-3-harbour':'Sail into Xero Emoji World'}
for i,(stem,line) in enumerate(LINES.items(),1):
    th=mp.THEMES[stem] if hasattr(mp,'THEMES') else None
    make(stem,th,line,f'{R}/promo/stories/xero-emoji-story-{i}-{stem.split("-",4)[-1]}.png')
