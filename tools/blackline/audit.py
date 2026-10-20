#!/usr/bin/env python3
"""Xero Emoji spec audit vs Unicode emoji-test.txt (UTS #51). Read-only on the repo.
Usage: audit.py [--repo PATH] [--emoji-test PATH_OR_URL] [--out DIR]
Exit 0 = all checks PASS, 1 = any FAIL, 2 = setup error."""
import os,re,csv,json,hashlib,collections,argparse,sys,urllib.request
ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--repo',default=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
ap.add_argument('--emoji-test',default='https://www.unicode.org/Public/emoji/latest/emoji-test.txt')
ap.add_argument('--out',default='.')
ap.add_argument('--map',default='packages/npm/emoji-map.json',help='emoji-map path relative to repo (falls back to demos/emoji-map.json)')
A=ap.parse_args()
R=os.path.abspath(A.repo);os.makedirs(A.out,exist_ok=True);os.chdir(A.out)
try:
    if re.match(r'https?://',A.emoji_test):
        raw=urllib.request.urlopen(A.emoji_test,timeout=60).read()
    else: raw=open(A.emoji_test,'rb').read()
    open('emoji-test.txt','wb').write(raw)
    for d in('svg','png'):assert os.path.isdir(f'{R}/{d}'),f'no {d}/ in {R}'
except Exception as e: print(f'setup error: {e}',file=sys.stderr);sys.exit(2)
REFVER=(re.search(rb'^# Version: (\S+)',raw,re.M) or [b'',b'?'])[1].decode()
REFSHA=hashlib.sha256(raw).hexdigest()
ref=[];allq={}
grp=sub=''
for l in open('emoji-test.txt',encoding='utf8'):
    if l.startswith('# group:'):grp=l[9:].strip();continue
    if l.startswith('# subgroup:'):sub=l[12:].strip();continue
    m=re.match(r'^([0-9A-F ]+?)\s*;\s*([\w-]+)\s*#\s*(\S+)\s+E(\S+)\s+(.*)$',l)
    if m:
        cps=[int(x,16) for x in m[1].split()];st=m[2]
        allq[tuple(cps)]=st
        if st=='fully-qualified':ref.append(dict(cps=cps,name=m[5].strip(),grp=grp,sub=sub,ver=m[4]))
def key(cps,strip=True):return '-'.join('%04x'%c for c in cps if not(strip and c==0xfe0f))
fq={key(r['cps']):r for r in ref}
fqfull={key(r['cps'],False):r for r in ref}
assert len(fq)==len(ref)
out={}
iss=collections.defaultdict(list)
for ext in('svg','png'):
    files=sorted(os.listdir(f'{R}/{ext}'))
    stems={};bad=[];empty=[];corrupt=[];hashes=collections.defaultdict(list)
    for f in files:
        p=f'{R}/{ext}/{f}';stem,e=os.path.splitext(f)
        if e!='.'+ext or not re.fullmatch(r'[0-9a-f]{2,6}(-[0-9a-f]{2,6})*',stem):bad.append(f);continue
        stems[stem]=f;b=open(p,'rb').read()
        if len(b)==0:empty.append(f)
        elif ext=='png' and not b.startswith(b'\x89PNG\r\n\x1a\n') or ext=='svg' and b'<svg' not in b[:4096]:corrupt.append(f)
        elif ext=='svg' and not b.rstrip().endswith(b'</svg>'):corrupt.append(f)
        hashes[hashlib.sha1(b).hexdigest()].append(f)
    fe=[s for s in stems if 'fe0f' in s.split('-')]
    missing=[k for k in fq if k not in stems]
    extra=[s for s in stems if s not in fq]
    out[ext]=dict(files=len(files),bad=bad,empty=empty,corrupt=corrupt,dups=[v for v in hashes.values() if len(v)>1],fe0f=fe,missing=missing,extra=extra,stems=stems)
# case-insensitive collisions not possible (lowercase enforced)
# metadata
mpp=f'{R}/{A.map}'
if not os.path.exists(mpp):mpp=f'{R}/demos/emoji-map.json'
mp=json.load(open(mpp)) if os.path.exists(mpp) else {}
namemis=[];charmis=[];mpmiss=[k for k in fq if k not in mp];mpextra=[k for k in mp if k not in fq]
for k,v in mp.items():
    if k in fq:
        r=fq[k];exp=''.join(map(chr,r['cps']))
        if v[1]!=exp:charmis.append((k,v[1].encode('unicode_escape').decode(),exp.encode('unicode_escape').decode()))
        if v[2]!=r['name']:namemis.append((k,v[2],r['name'],'emoji-map.json'))
        if v[3]!=r['grp'] or v[4]!=r['sub']:namemis.append((k,f'{v[3]}/{v[4]}',f"{r['grp']}/{r['sub']}",'emoji-map.json group'))
cp=f'{R}/qc/coverage.csv'
cov=list(csv.DictReader(open(cp,encoding='utf8'))) if os.path.exists(cp) else []
covnm=[]
for row in cov:
    k=key([int(x,16) for x in row['sequence'].split()]) if ' ' in row['sequence'] or True else None
    k=key([int(x,16) for x in re.split(r'[ _-]',row['sequence'].strip())])
    if k in fq:
        if row['name']!=fq[k]['name']:namemis.append((k,row['name'],fq[k]['name'],'qc/coverage.csv'))
    else: covnm.append(row['sequence'])
# categories
ZWJ=0x200d;SK=set(range(0x1f3fb,0x1f400));HAIR=set(range(0x1f9b0,0x1f9b4));TAG=set(range(0xe0020,0xe0080))
GEN={0x2640,0x2642};ARROW=0x27a1
cats={'zwj':lambda c:ZWJ in c,'skin_tone':lambda c:any(x in SK for x in c),
 'skin_tone_multi_person_mixed':lambda c:len({x for x in c if x in SK})>1,
 'hair':lambda c:any(x in HAIR for x in c) and len(c)>1,'keycap':lambda c:0x20e3 in c,
 'tag_subdivision_flag':lambda c:any(x in TAG for x in c),'fe0f_in_sequence':lambda c:0xfe0f in c,
 'gender':lambda c:any(x in GEN for x in c) and len(c)>1,'facing_right':lambda c:ARROW in c and ZWJ in c,
 'regional_flag':lambda c:all(0x1f1e6<=x<=0x1f1ff for x in c)}
catrows=[]
for n,f in cats.items():
    keys=[k for k,r in fq.items() if f(r['cps'])]
    ms=[k for k in keys if k not in out['svg']['stems'] or k not in out['png']['stems']]
    catrows.append((n,len(keys),len(keys)-len(ms),len(ms)))
# keycap form check / tag sequence structure check on files
struct=[]
for s in out['svg']['stems']:
    c=[int(x,16) for x in s.split('-')]
    if 0x20e3 in c and not (len(c)==2 and c[1]==0x20e3): struct.append((s,'keycap filename form'))
    if any(x in TAG for x in c) and not (c[0]==0x1f3f4 and c[-1]==0xe007f): struct.append((s,'tag seq form'))
    if ZWJ in c and (c[0]==ZWJ or c[-1]==ZWJ): struct.append((s,'dangling ZWJ'))
    if any(not(0<=x<=0x10ffff) or 0xd800<=x<=0xdfff for x in c): struct.append((s,'invalid code point'))
# ambiguous stripped keys: two FQ seqs collapse to same stem?
amb=len(fq)!=len(fqfull)
# svg vs png parity
sv=set(out['svg']['stems']);pn=set(out['png']['stems'])
W=lambda n,h,rows:csv.writer(open(n,'w',newline='')).writerows([h]+rows)
def det(k):r=fq.get(k);return [k,' '.join('%04X'%c for c in r['cps']),''.join(map(chr,r['cps'])),r['name'],r['grp'],r['sub'],r['ver']] if r else [k]
H=['stem','codepoints_fq','emoji','cldr_name','group','subgroup','version']
W('missing.csv',['format']+H,[[e]+det(k) for e in out for k in out[e]['missing']])
extras=[]
for e in out:
    for s in out[e]['extra']:
        try:c=tuple(int(x,16) for x in s.split('-'));st=allq.get(c,'not in emoji-test.txt')
        except:st='unparseable'
        extras.append([e,s,st])
    for b in out[e]['bad']:extras.append([e,b,'bad filename'])
W('extra.csv',['format','file_stem','status_in_emoji_test'],extras)
W('name-mismatches.csv',['stem','repo_value','cldr_value','source'],namemis)
W('char-mismatches.csv',['stem','repo_char','expected_char'],charmis)
W('file-issues.csv',['format','file','issue'],[[e,f,'empty'] for e in out for f in out[e]['empty']]+[[e,f,'corrupt'] for e in out for f in out[e]['corrupt']]+[[e,'|'.join(d),'duplicate content'] for e in out for d in out[e]['dups']]+[['svg',s,i] for s,i in struct]+[[e,s,'filename contains fe0f'] for e in out for s in out[e]['fe0f']])
W('category-coverage.csv',['category','expected_fq','present_svg_and_png','missing'],catrows)
summ=dict(expected=len(ref),ambiguous_fe0f_strip=amb,**{e:{k:(len(v) if not isinstance(v,int) else v) for k,v in out[e].items()} for e in out},svg_not_png=sorted(sv-pn),png_not_svg=sorted(pn-sv),map_entries=len(mp),map_missing=len(mpmiss),map_extra=len(mpextra),charmis=len(charmis),namemis=len(namemis),cov_rows=len(cov),cov_unmatched=len(covnm),struct=len(struct),cats=catrows,dupsamples={e:out[e]['dups'][:5] for e in out},namesamples=namemis[:8])
C={r[0]:r for r in catrows}
def cat(n):r=C[n];return ('PASS' if r[3]==0 else 'FAIL',f'{r[2]}/{r[1]} present, {r[3]} missing')
sv_,pn_=out['svg'],out['png']
fileok=not any(len(o[k]) for o in(sv_,pn_) for k in('bad','empty','corrupt'))
checks=[
 ('1','Coverage of FQ sequences',('PASS' if not sv_['missing'] and not pn_['missing'] and not sv_['extra'] and not pn_['extra'] and sv==pn else 'FAIL',f"svg missing {len(sv_['missing'])}/extra {len(sv_['extra'])}; png missing {len(pn_['missing'])}/extra {len(pn_['extra'])}; svg-only {len(sv-pn)}, png-only {len(pn-sv)}")),
 ('2','Code point <-> filename',('PASS' if fileok and not struct and not charmis and not mpmiss and not mpextra else 'FAIL',f"bad/empty/corrupt {sum(len(o[k]) for o in(sv_,pn_) for k in('bad','empty','corrupt'))}; structural {len(struct)}; map char mismatches {len(charmis)}; map missing {len(mpmiss)}/extra {len(mpextra)}")),
 ('3','ZWJ sequences',cat('zwj')),
 ('4','Skin-tone modifiers (incl. mixed)',(('PASS' if C['skin_tone'][3]==0 and C['skin_tone_multi_person_mixed'][3]==0 else 'FAIL'),cat('skin_tone')[1]+'; mixed '+cat('skin_tone_multi_person_mixed')[1])),
 ('5','Hair components',cat('hair')),('6','Keycaps',cat('keycap')),('7','Tag sequences',cat('tag_subdivision_flag')),
 ('8','FE0F consistency',('PASS' if not sv_['fe0f'] and not pn_['fe0f'] and C['fe0f_in_sequence'][3]==0 else 'FAIL',f"filenames containing fe0f: svg {len(sv_['fe0f'])}, png {len(pn_['fe0f'])}")),
 ('9','Gender / facing-right',(('PASS' if C['gender'][3]==0 and C['facing_right'][3]==0 else 'FAIL'),'gender '+cat('gender')[1]+'; facing-right '+cat('facing_right')[1])),
 ('10','Names vs CLDR',('PASS' if not namemis and not covnm and mp else 'FAIL',f"{len(namemis)} mismatches; {len(covnm)} unmatched coverage.csv rows; map {'found' if mp else 'NOT FOUND'}")),
]
dg={e:out[e]['dups'] for e in out}
summ['reference']=dict(source=A.emoji_test,version=REFVER,sha256=REFSHA);summ['repo']=R
summ['checks']={n:dict(name=t,result=r[0],detail=r[1]) for n,t,r in checks}
summ['passed']=sum(r[0]=='PASS' for _,_,r in checks)
json.dump(summ,open('summary.json','w'),indent=1,ensure_ascii=False)
L=[f'# Xero Emoji spec audit','',f'Repo: `{R}`  ',f'Reference: {A.emoji_test} (Version {REFVER}, sha256 {REFSHA[:12]}…)  ',f'Expected fully-qualified: {len(ref)}; SVG files {sv_["files"]}, PNG files {pn_["files"]}','',
 f'**Result: {summ["passed"]}/10 PASS**','','| # | Check | Result | Detail |','|-|-|-|-|']+[f'| {n} | {t} | {r[0]} | {r[1]} |' for n,t,r in checks]+['',
 '## Category coverage','','| Category | Expected | Present (svg+png) | Missing |','|-|-|-|-|']+[f'| {a} | {b} | {c} | {d} |' for a,b,c,d in catrows]+['',
 '## Duplicates (byte-identical content; INFO, not a FAIL)','']+[f'- {e}: {len(dg[e])} groups / {sum(map(len,dg[e]))} files' for e in dg]+['',
 'Details: missing.csv, extra.csv, name-mismatches.csv, char-mismatches.csv, file-issues.csv, category-coverage.csv, summary.json','']
open('REPORT.md','w').write('\n'.join(L))
for n,t,r in checks:print(f'{r[0]:4} {n:>2} {t}: {r[1]}')
print(f"{summ['passed']}/10 PASS")
sys.exit(0 if summ['passed']==10 else 1)
