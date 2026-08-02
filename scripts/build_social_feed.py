#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

def valid_url(v): return urlparse(str(v or '')).scheme in {'http','https'} and bool(urlparse(str(v or '')).netloc)
def freshness(published):
 try:
  d=datetime.fromisoformat(str(published).replace('Z','+00:00')); days=max(0,(datetime.now(timezone.utc)-d.astimezone(timezone.utc)).total_seconds()/86400); return max(0,1-days/30)
 except Exception:return 0

def score(c):
 e=c.get('engagementSnapshot') or {}; interaction=sum(float(e.get(k) or 0) for k in ('likes','replies','shares','upvotes'))
 return round(30*float(c.get('matchConfidence') or 0)+20*freshness(c.get('publishedAt'))+20*min(1,interaction/1000)+15*min(1,float(c.get('crossPlatformCount') or 0)/3)+10*min(1,(float(c.get('siteViews') or 0)+3*float(c.get('siteFavorites') or 0))/1000)+5*min(1,float(c.get('editorWeight') or 0)),3)
def build(queue,events):
 ids={str(e.get('id') or e.get('uid') or '') for e in events}; out=[]
 for c in queue:
  if c.get('reviewStatus')!='approved' or float(c.get('matchConfidence') or 0)<0.68 or str(c.get('matchedEventId') or '') not in ids or not valid_url(c.get('postUrl')): continue
  row={k:c.get(k) for k in ('candidateId','source','postUrl','publishedAt','shortExcerpt','matchedEventId','matchConfidence','keywords')}; row['popularityScore']=score(c); row['tag']='社群討論'; out.append(row)
 return sorted(out,key=lambda x:x['popularityScore'],reverse=True)[:12]
def main():
 p=argparse.ArgumentParser(); p.add_argument('--queue',default='data/social_review_queue.json'); p.add_argument('--events',default='data/exhibitions.curated.json'); p.add_argument('--output',default='data/social_discussions.json'); a=p.parse_args()
 q=json.loads(Path(a.queue).read_text(encoding='utf-8')).get('candidates',[]); ev=json.loads(Path(a.events).read_text(encoding='utf-8')); ev=ev.get('events',ev if isinstance(ev,list) else []); rows=build(q,ev)
 Path(a.output).write_text(json.dumps({'schemaVersion':1,'updatedAt':datetime.now(timezone.utc).isoformat(),'discussions':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'social discussions: {len(rows)}')
if __name__=='__main__': main()
