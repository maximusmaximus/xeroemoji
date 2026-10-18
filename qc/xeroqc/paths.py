"""Layout resolution for xeroqc and the reused checkers.
Workspace layout: <set>/{svg,png,qc,work}, LOCK-*.md in <set>/, coverage in <set>/../plan/coverage.csv.
Repo layout:      <repo>/{svg,png,qc}, checkers in qc/checkers/, locks in qc/locks/, coverage in qc/coverage.csv.
Overrides: XEROQC_SET (set root), XEROQC_COVERAGE (coverage.csv path)."""
import os,sys
def _find_set(start):
    """Set root = XEROQC_SET env var, else the nearest parent dir holding svg/ and qc/ (works in the workspace set/ and in the repo)."""
    e=os.environ.get('XEROQC_SET')
    if e: return os.path.abspath(e)
    d=os.path.dirname(os.path.abspath(start))
    while d!=os.path.dirname(d):
        if os.path.isdir(d+'/svg') and os.path.isdir(d+'/qc'): return d
        d=os.path.dirname(d)
    raise SystemExit('xeroqc: cannot find the set root (dir with svg/ and qc/); set XEROQC_SET')
SET=_find_set(__file__); QC=SET+'/qc'
WORK=SET+'/work' if os.path.isdir(SET+'/work') else QC+'/checkers'
ROOT=os.path.dirname(SET)
LOCKDIR=QC+'/locks' if os.path.isdir(QC+'/locks') else SET
def _coverage():
    for p in (os.environ.get('XEROQC_COVERAGE'),QC+'/coverage.csv',SET+'/plan/coverage.csv',ROOT+'/plan/coverage.csv'):
        if p and os.path.exists(p): return p
    raise SystemExit('xeroqc: coverage.csv not found; set XEROQC_COVERAGE')
COVERAGE=_coverage()
for p in (QC,WORK):
    if p not in sys.path: sys.path.insert(0,p)
os.environ.setdefault('XEROQC_SET',SET)   # the reused checkers resolve the same root
