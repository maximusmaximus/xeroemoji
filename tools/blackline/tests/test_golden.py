"""Golden regression: rebuild the golden set with both engines and compare to the approved references.
Sources: BL_SRC (env), default <repo>/svg (tools/blackline/../../svg). Each engine is held to the references it
produced in the approved (selected) build (golden/ref/engines.json)."""
import os,sys,subprocess,tempfile,pytest
H=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
SRC=os.path.abspath(os.environ.get('BL_SRC') or os.path.join(H,'..','..','svg'))
REF=os.path.join(H,'golden','ref')
@pytest.mark.skipif(not os.path.isdir(REF),reason='no approved golden references yet')
@pytest.mark.skipif(not os.path.isdir(SRC),reason=f'no colour sources at {SRC} (set BL_SRC)')
@pytest.mark.parametrize('engine',['vector','raster'])
def test_golden(engine):
    if engine=='raster':
        import shutil
        pt=os.environ.get('POTRACE') or shutil.which('potrace') or os.path.join(H,'tools','potrace')
        if not os.path.exists(pt): pytest.fail('raster engine needs potrace: run tools/get_potrace.sh or set POTRACE')
    out=tempfile.mkdtemp(); env=dict(os.environ,BL_SRC=SRC)
    b=subprocess.run([sys.executable,os.path.join(H,'pipeline.py'),'build','--engine',engine,'--src',SRC,'--out',out,
                      '--codes','@'+os.path.join(H,'golden','codes.txt')],capture_output=True,text=True,env=env)
    assert b.returncode==0 and '"errors": 0' in b.stdout, b.stdout[-1500:]+b.stderr[-1500:]
    r=subprocess.run([sys.executable,os.path.join(H,'pipeline.py'),'golden','test','--build',out,'--engine',engine],
                     capture_output=True,text=True,env=env)
    assert r.returncode==0, r.stdout+r.stderr[-1500:]
