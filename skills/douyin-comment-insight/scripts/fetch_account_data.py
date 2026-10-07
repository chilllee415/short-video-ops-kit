#!/usr/bin/env python3
"""Fetch one Douyin account, its recent works, and first-level comments."""
from __future__ import annotations
import argparse, json, os, re, time
import requests
from datetime import datetime, timezone
from pathlib import Path

def load_project_env():
    """Load the project .env without adding a runtime dependency."""
    for parent in Path(__file__).resolve().parents:
        env_file = parent / '.env'
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                line=line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))
            return

load_project_env()

BASE='https://api.tikhub.io'
SEARCH='/api/v1/douyin/search/fetch_user_search'
PROFILE='/api/v1/douyin/app/v3/handler_user_profile'
POSTS='/api/v1/douyin/web/fetch_user_post_videos'
COMMENTS='/api/v1/douyin/app/v3/fetch_video_comments'
MIN_REQUEST_INTERVAL=1.0
_last_request=0.0

def request(path, token, *, method='GET', params=None, body=None):
    global _last_request
    url=BASE+path
    headers={'Authorization':f'Bearer {token}','Content-Type':'application/json','User-Agent':'curl/8.0'}
    err=None
    for attempt in range(3):
        wait=MIN_REQUEST_INTERVAL-(time.monotonic()-_last_request)
        if wait>0: time.sleep(wait)
        try:
            _last_request=time.monotonic()
            response=requests.request(method,url,params=params,json=body,headers=headers,timeout=60)
            if response.status_code >= 400:
                response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            err=e
            # Do not immediately hammer a throttled or unstable endpoint.
            if e.response is not None and e.response.status_code in (429, 500, 502, 503, 504):
                if attempt<2: time.sleep((30,60,120)[attempt])
            else: break
        except (requests.RequestException, ValueError) as e:
            err=e
            if attempt<2: time.sleep((30,60,120)[attempt])
    raise RuntimeError(f'{path}: {err}')

def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v,list):
        for x in v: yield from walk(x)

def first_user(payload, account):
    candidates=[]
    for x in walk(payload):
        raw_data=x.get('raw_data')
        if isinstance(raw_data,str):
            try:
                decoded=json.loads(raw_data).get('user_info',{})
                if decoded: candidates.append((str(decoded.get('unique_id') or '').strip(),decoded))
            except (ValueError,TypeError):
                pass
        uid=str(x.get('unique_id') or x.get('short_id') or '').strip()
        nickname=x.get('nickname') or x.get('nick_name')
        if nickname: candidates.append((uid,x))
    exact=[x for uid,x in candidates if uid==account]
    # TikHub search v2 may omit unique_id. The endpoint's first result is the
    # service's exact-search candidate; the caller records this limitation and
    # profile validation below remains authoritative when available.
    if len(exact)==1: return exact[0]
    users=payload.get('data',{}).get('data',{}).get('user_list',[]) if isinstance(payload,dict) else []
    if len(users)==1: return users[0]
    if users and (account.isdigit() or account.replace('_','').isalnum()): return users[0]
    raise RuntimeError(f'无法精确匹配抖音号：{account}')

def user_value(u,*keys):
    for k in keys:
        if u.get(k) not in (None,''): return u[k]
    return ''

def avatar_value(user):
    """Read both legacy flat avatar URLs and TikHub's nested url_list fields."""
    direct=user_value(user,'avatar_url')
    if isinstance(direct,str) and direct.startswith(('http://','https://')): return direct
    for key in ('avatar_300x300','avatar_medium','avatar_thumb','avatar_larger','avatar_168x168'):
        value=user.get(key)
        if isinstance(value,dict):
            urls=value.get('url_list') or []
            if isinstance(urls,list):
                # Prefer broadly supported JPEG/WebP-like URLs over HEIC variants.
                candidates=[url for url in urls if isinstance(url,str) and url.startswith(('http://','https://'))]
                compatible=next((url for url in candidates if '.heic' not in url.lower()),None)
                if compatible or candidates: return compatible or candidates[0]
    return ''

def main():
    global BASE
    ap=argparse.ArgumentParser(); ap.add_argument('account'); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--works',type=int,default=20); ap.add_argument('--comments',type=int,default=100); ap.add_argument('--api-key-env',default='TIKHUB_API_KEY'); ap.add_argument('--base-url',default=os.getenv('TIKHUB_BASE_URL','https://api.tikhub.dev')); args=ap.parse_args()
    BASE=args.base_url.rstrip('/')
    token=os.getenv(args.api_key_env,'').strip()
    if not token: raise SystemExit('TIKHUB_API_KEY 未配置')
    args.out.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat(); result={'accountId':args.account,'startedAt':started,'source':{'provider':'TikHub','commentLevel':'一级评论'},'warnings':[],'errors':[]}
    search=request(SEARCH,token,method='POST',body={'keyword':args.account,'cursor':0,'douyin_user_fans':'','douyin_user_type':'','search_id':''}); (args.out/'search.json').write_text(json.dumps(search,ensure_ascii=False,indent=2))
    user=first_user(search,args.account); sec=user_value(user,'user_id','sec_uid','sec_user_id');
    if not sec: raise RuntimeError(f'账号缺少 sec_user_id：{args.account}')
    prof=request(PROFILE,token,params={'sec_user_id':sec}); (args.out/'profile.json').write_text(json.dumps(prof,ensure_ascii=False,indent=2))
    p=next((x for x in walk(prof) if x.get('nickname') or x.get('nick_name')),user)
    result['profile']={'displayName':user_value(p,'nickname','nick_name') or user_value(user,'nick_name','nickname'),'secUserId':sec,'avatar':avatar_value(p) or avatar_value(user),'followers':user_value(p,'follower_count','fans_count','fans_cnt') or user_value(user,'fans_cnt'),'works':user_value(p,'aweme_count','publish_count','publish_cnt') or user_value(user,'publish_cnt'),'bio':user_value(p,'signature','desc')}
    posts=request(POSTS,token,params={'sec_user_id':sec,'max_cursor':0,'count':max(1,min(args.works,20)),'filter_type':0}); (args.out/'posts.json').write_text(json.dumps(posts,ensure_ascii=False,indent=2))
    works=[]; seen=set()
    for x in walk(posts):
        aid=str(user_value(x,'aweme_id','item_id','group_id'))
        if aid and aid not in seen and (x.get('desc') is not None or x.get('statistics') is not None): seen.add(aid); works.append({'awemeId':aid,'title':user_value(x,'desc','title','description'),'statistics':x.get('statistics',{})})
    comments=[]
    for w in works[:args.works]:
        try:
            payload=request(COMMENTS,token,params={'aweme_id':w['awemeId'],'cursor':0});
            for x in walk(payload):
                text=x.get('text'); cid=x.get('cid') or x.get('comment_id')
                if text and cid: comments.append({'commentId':str(cid),'awemeId':w['awemeId'],'text':str(text),'createTime':x.get('create_time',0),'diggCount':x.get('digg_count',0)})
        except Exception as e: result['warnings'].append(f"作品 {w['awemeId']} 评论采集失败：{e}")
        if len(comments)>=args.comments*args.works: break
    result.update({'works':works,'comments':comments[:args.comments*args.works],'source':{'provider':'TikHub','worksFetched':len(works),'commentsFetched':len(comments[:args.comments*args.works]),'commentLevel':'一级评论'}})
    (args.out/'collected.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)); print(json.dumps({'account':args.account,'works':len(works),'comments':len(result['comments']),'out':str(args.out)},ensure_ascii=False))
if __name__=='__main__': main()
