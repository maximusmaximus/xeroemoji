import os,sys
ROOT='/workspace/xerographer-emojis'; SET=ROOT+'/set'; QC=SET+'/qc'; WORK=SET+'/work'
for p in (QC,WORK):
    if p not in sys.path: sys.path.insert(0,p)
