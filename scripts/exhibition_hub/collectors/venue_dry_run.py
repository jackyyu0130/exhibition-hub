from __future__ import annotations
import hashlib, json, re, time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse
import requests

DATE_RE=re.compile(r"(?P<y>20\d{2})[./年-](?P<m>\d{1,2})[./月-](?P<d>\d{1,2})")
RANGE_RE=re.compile(r"(?:(20\d{2})[./年-])?(\d{1,2})[./月-](\d{1,2}).{0,12}?(?:(20\d{2})[./年-])?(\d{1,2})[./月-](\d{1,2})")
SPACE_RE=re.compile(r"\s+")

def clean(v:Any)->str: return SPACE_RE.sub(' ',str(v or '')).strip()
def iso(y,m,d): return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
def dates(text:str):
 text=clean(text); r=RANGE_RE.search(text)
 if r:
  y1,m1,d1,y2,m2,d2=r.groups(); y1=int(y1 or y2 or 0); y2=int(y2 or y1 or 0)
  if y1 and y2: return iso(y1,m1,d1),iso(y2,m2,d2)
 m=DATE_RE.search(text)
 return (iso(*m.groups()),iso(*m.groups())) if m else ('','')

class BlockParser(HTMLParser):
 def __init__(self,base):
  super().__init__(convert_charrefs=True); self.base=base; self.stack=[]; self.blocks=[]; self.current=None; self.ignore=0
 def handle_starttag(self,tag,attrs):
  a={k.lower():str(v or '') for k,v in attrs}; tag=tag.lower()
  if tag in {'script','style','noscript','svg'}: self.ignore+=1; return
  if self.ignore:return
  if tag in {'article','li','tr','a'}:
   if self.current is None: self.current={'parts':[],'links':[],'images':[],'depth':0,'tag':tag}
   self.current['depth']+=1
  if self.current:
   if tag=='a' and a.get('href'): self.current['links'].append(urljoin(self.base,a['href']))
   if tag=='img':
    src=a.get('data-src') or a.get('data-original') or a.get('src')
    if src:self.current['images'].append(urljoin(self.base,src))
    if a.get('alt'):self.current['parts'].append(a['alt'])
 def handle_data(self,data):
  if not self.ignore and self.current and clean(data): self.current['parts'].append(clean(data))
 def handle_endtag(self,tag):
  tag=tag.lower()
  if tag in {'script','style','noscript','svg'} and self.ignore: self.ignore-=1; return
  if self.ignore or not self.current:return
  if tag in {'article','li','tr','a'}:
   self.current['depth']-=1
   if self.current['depth']<=0:
    self.blocks.append(self.current); self.current=None

def allowed(url:str,domains:list[str])->bool:
 host=urlparse(url).hostname or ''; host=host.lower()
 return any(host==d.lower() or host.endswith('.'+d.lower()) for d in domains)

def extract_candidates(html:str,profile:dict[str,Any],listing_url:str)->list[dict[str,Any]]:
 p=BlockParser(listing_url); p.feed(html); p.close(); out=[]; seen=set()
 req=[clean(x).lower() for x in profile.get('requiredKeywords',[])]; exc=[clean(x).lower() for x in profile.get('excludeKeywords',[])]
 patterns=[re.compile(x,re.I) for x in profile.get('detailUrlPatterns',[])]; domains=profile.get('allowedDomains',[])
 for b in p.blocks:
  text=clean(' '.join(b['parts'])); lower=text.lower()
  if len(text)<4 or any(x and x in lower for x in exc): continue
  if req and not any(x in lower for x in req): continue
  start,end=dates(text)
  links=[u for u in b['links'] if allowed(u,domains)]
  detail=next((u for u in links if not patterns or any(r.search(urlparse(u).path+'?'+urlparse(u).query) for r in patterns)),listing_url)
  if not start and not profile.get('allowUndatedCandidates',False): continue
  title=text
  title=re.sub(r'^(?:\d{1,2}[./-]\d{1,2}.*?)(?=[^0-9])','',title).strip(' -｜|') or text
  title=title[:180]
  key=(profile['sourceId'],title,start,detail)
  if key in seen: continue
  seen.add(key)
  out.append({'sourceId':profile['sourceId'],'sourceEventId':hashlib.sha256('|'.join(map(str,key)).encode()).hexdigest()[:24],
   'title':title,'startDate':start,'endDate':end,'detailUrl':detail,'listingUrl':listing_url,
   'imageUrl':b['images'][0] if b['images'] else '', 'venueName':profile.get('venueName',''),
   'region':profile.get('region',''),'category':profile.get('category','其他'),'candidateOnly':True})
 return out[:int(profile.get('maxCandidates',80))]

def run_profile(profile:dict[str,Any],session:requests.Session|None=None)->dict[str,Any]:
 if profile.get('mode')=='verify_only': return {'sourceId':profile['sourceId'],'status':'skipped','reason':'verify_only','candidates':[]}
 session=session or requests.Session(); candidates=[]; errors=[]; fetched=[]
 headers={'User-Agent':'TaiwanExhibitionJournal-DryRun/1.0 (+https://twexhibition.com/)'}
 for url in profile.get('listingUrls',[]):
  if not allowed(url,profile.get('allowedDomains',[])): errors.append(f'domain-not-allowed:{url}'); continue
  try:
   r=session.get(url,headers=headers,timeout=float(profile.get('timeoutSeconds',25))); r.raise_for_status(); fetched.append(url)
   candidates.extend(extract_candidates(r.text,profile,url)); time.sleep(float(profile.get('minDelaySeconds',0)))
  except Exception as e: errors.append(f'{type(e).__name__}:{e}')
 return {'sourceId':profile['sourceId'],'status':'success' if not errors else ('partial' if candidates else 'failed'),
  'candidateCount':len(candidates),'candidates':candidates,'errors':errors,'fetchedUrls':fetched,'publishAllowed':False,'publicDataWritten':False}

def load_profiles(path:Path,group:str)->list[dict[str,Any]]:
 d=json.loads(path.read_text(encoding='utf-8')); return list(d.get('groups',{}).get(group,[]))
