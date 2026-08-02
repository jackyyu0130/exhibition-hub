#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from exhibition_hub.collectors.venue_dry_run import load_profiles, run_profile

def main():
 p=argparse.ArgumentParser(); p.add_argument('--group',required=True); p.add_argument('--profiles',default='data/collector_profiles.json'); p.add_argument('--output-dir',default='collector-dry-run-output'); a=p.parse_args()
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); reports=[]
 for profile in load_profiles(Path(a.profiles),a.group):
  report=run_profile(profile); reports.append(report)
  (out/f"{profile['sourceId']}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 summary={'schemaVersion':1,'group':a.group,'generatedAt':datetime.now(timezone.utc).isoformat(),'publishAllowed':False,'publicDataWritten':False,
  'sourceCount':len(reports),'successCount':sum(r['status'] in {'success','partial','skipped'} for r in reports),'candidateCount':sum(r.get('candidateCount',0) for r in reports),'sources':[{k:r.get(k) for k in ('sourceId','status','candidateCount','errors')} for r in reports]}
 (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
 return 0
if __name__=='__main__': raise SystemExit(main())
