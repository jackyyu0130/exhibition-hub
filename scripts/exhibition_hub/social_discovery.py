from __future__ import annotations
import hashlib, json, math, re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SPACE=re.compile(r'\s+')
def clean(v): return SPACE.sub(' ',str(v or '')).strip()
def valid_public_url(url): return urlparse(str(url)).scheme in {'http','https'} and bool(urlparse(str(url)).netloc)
def tokens(text): return {x for x in re.findall(r'[A-Za-z0-9\u4e00-\u9fff]{2,}',clean(text).lower()) if len(x)>1}

def event_index(events):
 out=[]
 for e in events:
  text=' '.join(clean(e.get(k)) for k in ('title','locationName','venueGroup','unit','description'))
  out.append((str(e.get('id') or e.get('uid') or ''),tokens(text),clean(e.get('title'))))
 return out

def match_candidate(candidate,events):
 ct=tokens(' '.join([clean(candidate.get('shortExcerpt')),clean(candidate.get('keywords'))])); best=('',0.0,[])
 for eid,et,title in event_index(events):
  if not eid or not et: continue
  overlap=ct & et; score=len(overlap)/max(3,min(len(ct or {1}),len(et)))
  if title and clean(title).lower() in clean(candidate.get('shortExcerpt')).lower(): score=max(score,0.88)
  if score>best[1]: best=(eid,min(0.99,score),sorted(overlap)[:10])
 return best

def normalize_candidate(raw,source):
 excerpt=clean(raw.get('shortExcerpt') or raw.get('title'))[:240]
 url=clean(raw.get('postUrl'))
 if not excerpt or not valid_public_url(url): raise ValueError('candidate requires public URL and excerpt')
 payload={'source':source,'postUrl':url,'authorDisplay':'公開來源（已匿名）','publishedAt':clean(raw.get('publishedAt')),
  'shortExcerpt':excerpt,'engagementSnapshot':raw.get('engagementSnapshot') or {},'matchedEventId':'','matchConfidence':0.0,'matchSignals':[],
  'keywords':raw.get('keywords') or [],'reviewStatus':'pending','crossPlatformCount':0,'siteViews':0,'siteFavorites':0,'editorWeight':0,'popularityScore':0.0}
 payload['candidateId']=hashlib.sha256((source+'|'+url).encode()).hexdigest()[:24]; return payload

def score(candidate):
 confidence=float(candidate.get('matchConfidence') or 0); engagement=candidate.get('engagementSnapshot') or {}
 interaction=sum(float(engagement.get(k) or 0) for k in ('likes','replies','shares','upvotes'))
 return round(30*confidence+20*min(1,interaction/1000)+15*min(1,float(candidate.get('crossPlatformCount') or 0)/3)+10*min(1,(float(candidate.get('siteViews') or 0)+3*float(candidate.get('siteFavorites') or 0))/1000)+5*min(1,float(candidate.get('editorWeight') or 0)),3)

def build_queue(manual,events):
 rows=[]
 for raw in manual:
  source=clean(raw.get('source')).lower()
  if source not in {'threads','ptt','dcard','manual'}: continue
  c=normalize_candidate(raw,source); eid,conf,signals=match_candidate(c,events); c.update(matchedEventId=eid,matchConfidence=round(conf,3),matchSignals=signals); c['popularityScore']=score(c); rows.append(c)
 return rows
