#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests

KEYWORDS=re.compile(r'演唱會|音樂會|音樂祭|festival|concert|live|展覽|展演|活動|巡迴|tour|fan.?meeting|公演|售票|節目',re.I)
DATE=re.compile(r'(20\d{2})[./年-](\d{1,2})[./月-](\d{1,2})')
class Links(HTMLParser):
 def __init__(self,base): super().__init__(convert_charrefs=True); self.base=base; self.href=''; self.parts=[]; self.rows=[]; self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in {'script','style','noscript','svg'}: self.skip+=1
  if not self.skip and tag=='a': self.href=dict(attrs).get('href',''); self.parts=[]
 def handle_data(self,data):
  if self.href and not self.skip: self.parts.append(data)
 def handle_endtag(self,tag):
  if tag in {'script','style','noscript','svg'} and self.skip: self.skip-=1
  if tag=='a' and self.href and not self.skip:
   text=' '.join(' '.join(self.parts).split()); url=urljoin(self.base,self.href); self.rows.append((url,text)); self.href=''; self.parts=[]
def allowed(url,base):
 h=urlparse(url).hostname or ''; b=urlparse(base).hostname or ''; return h==b or h.endswith('.'+b) or b.endswith('.'+h)
def iso(m): return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if m else ''
def main():
 p=argparse.ArgumentParser(); p.add_argument('--catalog',default='data/c3_source_catalog.json'); p.add_argument('--group',default='all'); p.add_argument('--output-dir',default='c3-source-artifacts'); p.add_argument('--limit',type=int,default=24); p.add_argument('--offset',type=int,default=0); a=p.parse_args()
 cat=json.loads(Path(a.catalog).read_text(encoding='utf-8')); sources=[s for s in cat.get('sources',[]) if s.get('automatedPublicRead') and (a.group=='all' or s.get('category')==a.group)][a.offset:a.offset+a.limit]
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); summary=[]; session=requests.Session(); headers={'User-Agent':'TaiwanExhibitionJournal-C3Discovery/1.0 (+https://twexhibition.com/)'}
 for s in sources:
  ep=next((e for e in s.get('endpoints',[]) if e.get('platform')=='website' and e.get('url')),None); candidates=[]; errors=[]; fetched=[]
  if ep:
   try:
    r=session.get(ep['url'],headers=headers,timeout=20); r.raise_for_status(); fetched.append(r.url); parser=Links(r.url); parser.feed(r.text)
    seen=set()
    for url,text in parser.rows:
     if not allowed(url,r.url) or not KEYWORDS.search(text) or len(text)<4: continue
     key=(s['id'],url,text); cid=hashlib.sha256('|'.join(key).encode()).hexdigest()[:24]
     if cid in seen: continue
     seen.add(cid); dm=DATE.search(text)
     candidates.append({'candidateId':cid,'sourceId':s['id'],'candidateOrigin':'source_catalog','title':text[:220],'startDate':iso(dm),'endDate':iso(dm),'venueName':s['name'] if s.get('category')=='livehouse' else '','region':s.get('region',''),'sourceUrl':url,'category':'演唱會' if s.get('category') in {'ticketing','organizer','livehouse','festival'} else '其他','candidateOnly':True})
     if len(candidates)>=20: break
   except Exception as e: errors.append(f'{type(e).__name__}:{e}')
  report={'sourceId':s['id'],'status':'success' if not errors else ('partial' if candidates else 'failed'),'candidateCount':len(candidates),'candidates':candidates,'errors':errors,'fetchedUrls':fetched,'publishAllowed':False,'publicDataWritten':False}
  (out/f"{s['id']}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); summary.append({k:report[k] for k in ('sourceId','status','candidateCount','errors')}); time.sleep(.5)
 payload={'schemaVersion':1,'generatedAt':datetime.now(timezone.utc).isoformat(),'group':a.group,'sourceCount':len(summary),'candidateCount':sum(x['candidateCount'] for x in summary),'publishAllowed':False,'sources':summary}; (out/'summary.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
