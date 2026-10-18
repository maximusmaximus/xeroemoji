"""python -m xeroqc run [--jobs N] [--out DIR] [cp ...]   |   python -m xeroqc requirements   |   python -m xeroqc version   |   python -m xeroqc bootstrap-exceptions RESULTS.json"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xeroqc import VERSION
def main(a):
    if not a or a[0] in ('-h','--help'): print(__doc__); return 0
    if a[0]=='version': print('xeroqc',VERSION); return 0
    if a[0]=='requirements':
        from xeroqc import requirements as RQ
        for r in RQ.REQ: print(f"| {r['id']} | {r['title']} | {r['severity']} | {r['weight']} | {r['applies']} | {r['test']} |")
        return 0
    if a[0]=='bootstrap-exceptions':
        from xeroqc import exceptions as X
        E=X.bootstrap(a[1]); print('known exceptions',len(E)); return 0
    if a[0]=='run':
        jobs=7; out=None; files=[]
        for x in a[1:]:
            if x.startswith('--jobs='): jobs=int(x[7:])
            elif x.startswith('--out='): out=x[6:]
            else: files.append(x)
        from xeroqc import runner
        o,meta,sc,R=runner.run(files or None,jobs,out)
        import collections; c=collections.Counter(r['grade'] for r in R)
        print('xeroqc',VERSION,'->',o); print(dict(c))
        return 1 if c.get('FAIL') else 0
    print(__doc__); return 2
if __name__=='__main__': sys.exit(main(sys.argv[1:]))
