import json,csv,collections,html,statistics
def write(out,meta,sc,reqs,R):
    json.dump({'meta':meta,'set_checks':sc,'requirements':reqs,'results':R},open(f'{out}/results.json','w'),indent=1,sort_keys=False)
    with open(f'{out}/results.csv','w',newline='',encoding='utf-8') as fh:
        w=csv.writer(fh); ids=[r['id'] for r in reqs]
        w.writerow(['cp','name','group','subgroup','grade','score','score_strict','hard_fails','soft_fails','known_exceptions']+ids+['reasons'])
        for r in R:
            w.writerow([r['cp'],r['name'],r['group'],r['subgroup'],r['grade'],r['score'],r['score_strict'],' '.join(r['hard_fails']),' '.join(r['soft_fails']),' '.join(r['known_exceptions'])]
                       +[r['results'][i]['status'] for i in ids]+['; '.join(f"{k}: {v['reason']}" for k,v in r['results'].items() if v['status'] in ('FAIL',) )])
    open(f'{out}/summary.md','w',encoding='utf-8').write(summary(meta,sc,reqs,R))
    open(f'{out}/report.html','w',encoding='utf-8').write(htmlrep(meta,sc,reqs,R))
def stats(R):
    s=[r['score'] for r in R]; st=[r['score_strict'] for r in R]
    q=lambda v,p: sorted(v)[min(len(v)-1,int(p*len(v)))]
    return {'mean':round(statistics.mean(s),2),'median':q(s,.5),'min':min(s),'p5':q(s,.05),'max':max(s),'n100':sum(1 for x in s if x==100),
            'strict_mean':round(statistics.mean(st),2),'strict_min':min(st)}
def summary(meta,sc,reqs,R):
    G=collections.Counter(r['grade'] for r in R); L=[]
    L.append(f"# xeroqc results: {meta['timestamp']}\n")
    L.append(f"Tool xeroqc {meta['version']} (tool_md5 `{meta['tool_md5']}`), {meta['n_files']} emoji, {len(reqs)} scored requirements. "
             f"Locks: {meta['lock_state']['active_locks']} active, verify_locks {meta['lock_state'].get('verify_locks')}. Spec: qc/REQUIREMENTS.md.\n")
    L.append('## Grades\n| grade | emoji |\n|---|---|')
    for g in ('PASS','PASS-with-known-exceptions','FAIL'): L.append(f'| {g} | {G.get(g,0)} |')
    S=stats(R)
    L.append(f"\n## Score (0-100, weighted passes over applicable requirements; known exceptions count as met)\nmean {S['mean']}, median {S['median']}, min {S['min']}, 5th pct {S['p5']}, max {S['max']}; {S['n100']} emoji at 100. "
             f"Strict score (known exceptions not counted as met): mean {S['strict_mean']}, min {S['strict_min']}.\n")
    bins=collections.Counter(min(9,int(r['score']//10)) for r in R)
    L.append('| score | emoji |\n|---|---|'); L+= [f'| {b*10}-{b*10+9 if b<9 else 100} | {bins.get(b,0)} |' for b in range(9,-1,-1) if bins.get(b)]
    L.append('\n## By group\n| group | emoji | PASS | PASS-known | FAIL | mean score |\n|---|---|---|---|---|---|')
    by=collections.defaultdict(list)
    for r in R: by[r['group']].append(r)
    for g,v in sorted(by.items()):
        c=collections.Counter(x['grade'] for x in v)
        L.append(f"| {g} | {len(v)} | {c.get('PASS',0)} | {c.get('PASS-with-known-exceptions',0)} | {c.get('FAIL',0)} | {statistics.mean(x['score'] for x in v):.2f} |")
    L.append('\n## Requirements: results\n| id | title | sev | w | applicable | pass | known-exc | fail |\n|---|---|---|---|---|---|---|---|')
    for q in reqs:
        c=collections.Counter(r['results'][q['id']]['status'] for r in R)
        L.append(f"| {q['id']} | {q['title']} | {q['severity']} | {q['weight']} | {len(R)-c.get('N/A',0)} | {c.get('PASS',0)} | {c.get('KNOWN-EXCEPTION',0)} | {c.get('FAIL',0)} |")
    L.append('\n## Set-level checks')
    for k,v in sc.items(): L.append(f"- {k}: **{v['status']}** {json.dumps({a:b for a,b in v.items() if a!='status'})[:300]}")
    top=collections.Counter(k for r in R for k in r['hard_fails']+r['soft_fails'])
    L.append('\n## Top failing requirements\n| id | emoji failing |\n|---|---|'); L+=[f'| {k} | {n} |' for k,n in top.most_common()]
    F=[r for r in R if r['grade']=='FAIL']
    L.append(f'\n## Every FAIL ({len(F)}), with reasons (hard fails decide the grade; soft fails listed too)\n| cp | name | group | score | reasons |\n|---|---|---|---|---|')
    for r in F:
        why='; '.join(f"{k}: {r['results'][k]['reason']}" for k in r['hard_fails']+r['soft_fails'])
        L.append(f"| {r['cp']} | {r['name']} | {r['group']} | {r['score']} | {why} |")
    SF=[r for r in R if r['grade']!='FAIL' and r['soft_fails']]
    L.append(f'\n## Passing emoji with soft fails ({len(SF)})\n| cp | name | score | soft fails |\n|---|---|---|---|')
    for r in SF: L.append(f"| {r['cp']} | {r['name']} | {r['score']} | {'; '.join(k+': '+r['results'][k]['reason'] for k in r['soft_fails'])} |")
    K=collections.Counter(k for r in R for k in r['known_exceptions'])
    L.append('\n## Known exceptions (accepted, do not fail)\n| id | emoji |\n|---|---|'); L+=[f'| {k} | {n} |' for k,n in K.most_common()]
    return '\n'.join(L)+'\n'
def htmlrep(meta,sc,reqs,R):
    G=collections.Counter(r['grade'] for r in R); col={'PASS':'#1a7a1a','PASS-with-known-exceptions':'#a07000','FAIL':'#c01010'}
    rows=''.join(f"<tr><td><img src='../../../png/{r['cp']}.png' width=32 height=32></td><td>{r['cp']}</td><td>{html.escape(r['name'])}</td><td>{html.escape(r['group'])}</td>"
                 f"<td style='color:{col[r['grade']]}'>{r['grade']}</td><td>{r['score']}</td><td>{html.escape('; '.join(k+': '+r['results'][k]['reason'] for k in r['hard_fails']+r['soft_fails']))}</td></tr>"
                 for r in sorted(R,key=lambda r:({'FAIL':0,'PASS-with-known-exceptions':1,'PASS':2}[r['grade']],r['score'],r['cp'])))
    return (f"<!doctype html><meta charset=utf-8><title>xeroqc {meta['timestamp']}</title><style>body{{font:13px sans-serif}}td{{padding:2px 6px;border-bottom:1px solid #eee}}</style>"
            f"<h1>xeroqc {meta['version']} - {meta['timestamp']}</h1><p>"+' | '.join(f"<b style='color:{col[g]}'>{g}</b> {G.get(g,0)}" for g in col)+
            f"</p><p>tool_md5 {meta['tool_md5']}</p><table><tr><th></th><th>cp</th><th>name</th><th>group</th><th>grade</th><th>score</th><th>fails</th></tr>{rows}</table>")
