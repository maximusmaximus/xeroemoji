"""xeroqc - Xero Emoji house-requirements QC scorer (see qc/REQUIREMENTS.md).
Reuses the set's existing checkers: qc/check.py (metrics + house-spec ranges), work/hlaudit.py (fixed tool of record +
known exceptions), work/hatfit.py, work/posecheck.py, work/mouthbowl.py, the active lock list in qc/verify_locks.sh,
and the people_qc.py headwear rule. Read-only on the art."""
VERSION='1.0.0'
