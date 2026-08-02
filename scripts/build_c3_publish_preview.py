#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exhibition_hub.c3_review import apply_decisions, event_list, load_json, clean

CATEGORY_TO_CONTENT={
 '演唱會':'concert','音樂':'concert','表演':'performance','舞蹈':'performance','電影':'film_screening',
 '美術':'art_exhibition','設計':'exhibition','動漫':'pop_culture','市集':'market','快閃店':'popup','其他':'exhibition'
}

def stable_id(row:dict[str,Any])->str:
    return 'c3-'+hashlib.sha256(f"{row.get('sourceId')}|{row.get('sourceUrl')}|{row.get('title')}|{row.get('startDate')}".encode()).hexdigest()[:20]

def event_from_candidate(row:dict[str,Any])->dict[str,Any]:
    category=clean(row.get('category') or '其他')
    return {
      'id':stable_id(row),'title':clean(row.get('title')),'startDate':clean(row.get('startDate')),'endDate':clean(row.get('endDate') or row.get('startDate')),
      'category':category,'categories':[category],'contentType':CATEGORY_TO_CONTENT.get(category,'exhibition'),'contentTypes':[CATEGORY_TO_CONTENT.get(category,'exhibition')],
      'region':clean(row.get('region')).replace('臺','台'),'regionCanonical':clean(row.get('region')).replace('台','臺'),
      'location':clean(row.get('venueName')),'locationName':clean(row.get('venueName')),'venueName':clean(row.get('venueName')),'venueNames':[clean(row.get('venueName'))] if clean(row.get('venueName')) else [],
      'venueGroup':clean(row.get('venueName')),'venueDetail':'','address':clean(row.get('address')),'price':clean(row.get('price')) or '票價請見活動頁面',
      'unit':clean(row.get('organizer') or row.get('sourceName')),'description':clean(row.get('shortDescription')) or '此活動由 C3 候選審核流程加入，請以官方活動頁為準。',
      'source':clean(row.get('sourceName')),'sourceUrl':clean(row.get('sourceUrl')),'officialUrl':clean(row.get('sourceUrl')),
      'image':clean(row.get('imageUrl')),'images':[clean(row.get('imageUrl'))] if clean(row.get('imageUrl')) else [],
      'editorialStatus':'candidate','eventFormat':'physical','sourceUrlVerified':True,
      'c3Review':{'candidateId':row.get('candidateId'),'qualityScore':row.get('qualityScore'),'reviewStatus':'approved','reviewNotes':row.get('reviewNotes',''),'evidenceUrl':row.get('evidenceUrl','')},
      'sourceRecords':[{'sourceId':row.get('sourceId'),'sourceEventId':row.get('candidateId'),'priority':85,'officialUrl':row.get('sourceUrl')}]
    }

def merge_update(existing:dict[str,Any],row:dict[str,Any])->dict[str,Any]:
    result=deepcopy(existing)
    # C3 may fill blanks, but never replaces populated core fields from a lower-evidence candidate.
    fill={'image':row.get('imageUrl'),'price':row.get('price'),'unit':row.get('organizer'),'description':row.get('shortDescription'),'address':row.get('address')}
    for key,value in fill.items():
        if clean(value) and not clean(result.get(key)):
            result[key]=clean(value)
    urls=list(dict.fromkeys([*[u for u in result.get('sourceUrls',[]) if clean(u)],clean(row.get('sourceUrl'))]))
    result['sourceUrls']=[u for u in urls if u]
    result['c3Review']={'candidateId':row.get('candidateId'),'qualityScore':row.get('qualityScore'),'reviewStatus':'approved','reviewNotes':row.get('reviewNotes',''),'evidenceUrl':row.get('evidenceUrl','')}
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--queue',default='c3-review-artifact/c3_candidate_queue.json'); p.add_argument('--decisions',default='data/c3_review_decisions.json'); p.add_argument('--base',default='data/exhibitions.enriched.json'); p.add_argument('--output',default='c3-release-preview/exhibitions.enriched.preview.json'); p.add_argument('--audit',default='c3-release-preview/c3-release-audit.json'); a=p.parse_args()
    queue=load_json(a.queue,{'candidates':[]}).get('candidates',[]); decisions=load_json(a.decisions,{'decisions':[]}); reviewed=apply_decisions(queue,decisions)
    base_payload=load_json(a.base,{'events':[]}); events=deepcopy(event_list(base_payload)); index={clean(e.get('id') or e.get('uid')):i for i,e in enumerate(events)}
    approved=[]; skipped=[]; added=0; updated=0
    for row in reviewed:
        if row.get('reviewStatus')!='approved' or not row.get('publishEligible') or row.get('blockingIssues'):
            skipped.append({'candidateId':row.get('candidateId'),'reason':'not_approved_or_not_eligible'}); continue
        if row.get('sourceKind')=='manual' or 'social_only_evidence' in row.get('qualityFlags',[]):
            skipped.append({'candidateId':row.get('candidateId'),'reason':'social_or_manual_only_requires_secondary_official_evidence'}); continue
        match=row.get('existingMatch') or {}; event_id=clean(match.get('eventId'))
        if event_id and event_id in index:
            events[index[event_id]]=merge_update(events[index[event_id]],row); updated+=1
        else:
            event=event_from_candidate(row); index[event['id']]=len(events); events.append(event); added+=1
        approved.append(row.get('candidateId'))
    payload=deepcopy(base_payload) if isinstance(base_payload,dict) else {'events':[]}; payload['events']=events; payload['updatedAt']=datetime.now(timezone.utc).isoformat(); payload['c3ReleaseBuild']={'mode':'preview','published':False,'approvedCandidateIds':approved,'addedCount':added,'updatedCount':updated}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit={'schemaVersion':1,'preparedAt':datetime.now(timezone.utc).isoformat(),'published':False,'pullRequestPrepared':False,'baseEventCount':len(event_list(base_payload)),'previewEventCount':len(events),'approvedCount':len(approved),'addedCount':added,'updatedCount':updated,'skipped':skipped,'approvedCandidateIds':approved}
    audit_path=Path(a.audit); audit_path.parent.mkdir(parents=True,exist_ok=True); audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
