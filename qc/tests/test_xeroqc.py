"""Unit tests for xeroqc.  Run:  cd set/qc && python3 -m unittest discover -s tests -v"""
import os,sys,shutil,tempfile,unittest,json
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xeroqc import runner, requirements as RQ, VERSION
from xeroqc.paths import SET
from PIL import Image
class XQ(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        runner.prepare(sorted(x[:-4] for x in os.listdir(SET+'/svg') if x.endswith('.svg')))
        cls.tmp=tempfile.mkdtemp(prefix='xeroqc-test-')
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)
    def test_registry(self):
        ids=[r['id'] for r in RQ.REQ]
        self.assertEqual(len(ids),len(set(ids)))
        for r in RQ.REQ:
            self.assertIn(r['severity'],('hard','soft')); self.assertGreater(r['weight'],0); self.assertTrue(r['test'])
        self.assertTrue(VERSION)
    def test_known_good(self):
        r=runner.evaluate('1f600')                       # grinning face, original house art
        self.assertEqual(r['grade'],'PASS'); self.assertEqual(r['score'],100.0)
        self.assertEqual(r['results']['XQ-LOCK-02']['status'],'PASS')
    def test_known_good_people(self):
        r=runner.evaluate('1f6b6-1f3fd-200d-2640-200d-27a1')   # skeleton-first walker (batch 08 v2)
        self.assertEqual(r['grade'],'PASS'); self.assertEqual(r['results']['XQ-POSE-01']['status'],'PASS')
        self.assertEqual(r['results']['XQ-TONE-01']['status'],'PASS')
    def test_known_exception(self):
        r=runner.evaluate('1f404')                       # cow: highlight on outline, on the hlaudit known-exception list
        self.assertEqual(r['grade'],'PASS-with-known-exceptions')
        self.assertEqual(r['results']['XQ-HL-01']['status'],'KNOWN-EXCEPTION'); self.assertEqual(r['score'],100.0)
        self.assertLess(r['score_strict'],100.0)
    def test_exception_is_md5_pinned(self):
        s=open(SET+'/svg/1f404.svg').read().replace('</svg>','<!-- edited --></svg>')
        sp=os.path.join(self.tmp,'1f404.svg'); open(sp,'w').write(s)
        r=runner.evaluate('1f404',svg_path=sp,png_path=SET+'/png/1f404.png')
        self.assertEqual(r['results']['XQ-HL-01']['status'],'FAIL')    # a changed file loses its exception
        self.assertEqual(r['grade'],'FAIL')
    def test_synthetic_bad(self):
        sp=os.path.join(self.tmp,'1f600.svg'); pp=os.path.join(self.tmp,'1f600.png')
        open(sp,'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><rect width="100" height="50" fill="url(#nope)"/>'
                           '<text x="10" y="30" font-family="DejaVu Sans">hi</text></svg>')
        Image.new('RGB',(256,256),'white').save(pp)
        r=runner.evaluate('1f600',svg_path=sp,png_path=pp)
        self.assertEqual(r['grade'],'FAIL')
        for k in ('XQ-SVG-01','XQ-SVG-02','XQ-SVG-03','XQ-PNG-01','XQ-LOCK-02'):
            self.assertEqual(r['results'][k]['status'],'FAIL',k)
        self.assertLess(r['score'],60)
    def test_deterministic(self):
        a=runner.evaluate('1f937'); b=runner.evaluate('1f937')
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        self.assertEqual(a['results']['XQ-HAND-02']['status'],'KNOWN-EXCEPTION')   # Max declined the 2.3 stroke fix
if __name__=='__main__': unittest.main()
