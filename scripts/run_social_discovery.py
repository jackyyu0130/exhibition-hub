#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,re,requests
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin
from exhibition_hub.social_discovery import build_queue,normalize_candidate

def ptt_candidates(config):
 rows=[]
 for board in config.get('boards',[]):
  url=f'https://www.ptt.cc/bbs/{board}/index.html'
  try:
   r=requests.get(url,headers={'User-Agent':'TaiwanExhibitionJournal-SocialDiscovery/1.0'},timeout=20); r.raise_for_status()
   for href,title in re.findall(r'<a href="([^"]+)">([^<]+)</a>',r.text):
    if '/M.' not in href: continue
    rows.append({'source':'ptt','postUrl':urljoin(url,href),'shortExcerpt':title,'publishedAt':'','keywords':[board]})
  except Exception: continue
 return rows[:int(config.get('maxCandidatesPerRun',40))]

def main():
 p=argparse.ArgumentParser(); p.add_argument('--sources',default='data/social_sources.json'); p.add_argument('--manual',default='data/social_manual_candidates.json'); p.add_argument('--events',default='data/exhibitions.curated.json'); p.add_argument('--output',default='social-review-artifact/social_review_queue.json'); a=p.parse_args()
 cfg=json.loads(Path(a.sources).read_text(encoding='utf-8')); manual=json.loads(Path(a.manual).read_text(encoding='utf-8')).get('candidates',[])
 ptt=next((x for x in cfg['sources'] if x['id']=='ptt'),{}); collected=list(manual)
 if ptt.get('enabled'): collected.extend(ptt_candidates(ptt))
 # Threads only via official token/API; Dcard only via written authorization/manual import. No hidden scraping.
 events=json.loads(Path(a.events).read_text(encoding='utf-8')); events=events.get('events',events if isinstance(events,list) else [])
 queue=build_queue(collected,events); payload={'schemaVersion':1,'generatedAt':datetime.now(timezone.utc).isoformat(),'reviewRequired':True,'publishAllowed':False,'candidates':queue}
 out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'candidateCount':len(queue),'publishAllowed':False},ensure_ascii=False))
if __name__=='__main__': main()
