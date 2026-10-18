# Repo plan (staged locally, not pushed)
- Name: `xeroemoji` (does not exist yet on github.com/maximusmaximus; checked read-only 2026-10-18).
- Visibility: **not decided** (Max's call). Nothing has been created remotely and no remote is configured.
- Size: svg 102 MB + png 252 MB (7,926 files, largest 116 KB); whole repo ~373 MB / 8,034 files.
  No file is near GitHub's 100 MB limit and the total is well under the ~1 GB guidance, so **Git LFS is not needed**.
  (Consider LFS for png/ only if the PNGs will be re-rendered often, since every re-render adds the full binary to history.)
- Before pushing: confirm the commit author email, choose visibility, repoint qc/xeroqc/paths.py to the repo layout, confirm the README bio and the commercial-license contact.
