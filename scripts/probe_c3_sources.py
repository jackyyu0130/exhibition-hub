#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--catalog',default='data/c3_source_catalog.json'); p.add_argument('--output',default='c3-review-artifact/source-probe.json'); p.add_argument('--group',default='all'); p.add_argument('--limit',type=int,default=24); p.add_argument('--offset',type=int,default=0); a=p.parse_args()
    catalog=json.loads(Path(a.catalog).read_text(encoding='utf-8')); rows=[]
    auto=[s for s in catalog.get('sources',[]) if s.get('automatedPublicRead') and (a.group=='all' or s.get('category')==a.group)]
    selected=auto[a.offset:a.offset+a.limit]
    session=requests.Session(); headers={'User-Agent':'TaiwanExhibitionJournal-C3SourceAudit/1.0 (+https://twexhibition.com/)'}
    for source in selected:
        endpoint=next((e for e in source.get('endpoints',[]) if e.get('platform')=='website' and e.get('url')),None)
        if not endpoint: continue
        url=endpoint['url']; status='unreachable'; code=None; error=''
        try:
            r=session.get(url,headers=headers,timeout=18,allow_redirects=True); code=r.status_code
            status='reachable' if 200 <= r.status_code < 400 else 'blocked_or_error'
        except Exception as exc: error=f'{type(exc).__name__}:{exc}'
        rows.append({'sourceId':source['id'],'name':source['name'],'url':url,'host':urlparse(url).hostname,'status':status,'httpStatus':code,'error':error,'verificationOnly':True,'publishAllowed':False})
        time.sleep(0.5)
    payload={'schemaVersion':1,'generatedAt':datetime.now(timezone.utc).isoformat(),'group':a.group,'offset':a.offset,'limit':a.limit,'totalAutomatedSources':len(auto),'checkedCount':len(rows),'publishAllowed':False,'sources':rows}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'checkedCount':len(rows),'publishAllowed':False},ensure_ascii=False))
    return 0
if __name__=='__main__': raise SystemExit(main())
