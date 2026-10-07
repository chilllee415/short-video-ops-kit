#!/usr/bin/env python3
"""Batch collector entrypoint; analysis is completed by Codex from the emitted inputs."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--accounts',nargs='+',required=True); ap.add_argument('--workdir',type=Path,required=True); ap.add_argument('--works',type=int,default=20); ap.add_argument('--comments',type=int,default=100); args=ap.parse_args()
    results=[]
    for account in args.accounts:
        out=args.workdir/account
        cmd=[sys.executable,str(Path(__file__).with_name('fetch_account_data.py')),account,'--out',str(out),'--works',str(args.works),'--comments',str(args.comments)]
        try:
            raw=subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True); collected=out/'collected.json'; model=out/'analysis-input.json'
            subprocess.check_call([sys.executable,str(Path(__file__).with_name('analyze_comments.py')),'--input',str(collected),'--output',str(model)])
            results.append({'accountId':account,'status':'collected','analysisInput':str(model),'log':raw.splitlines()[-1] if raw else ''})
        except subprocess.CalledProcessError as e: results.append({'accountId':account,'status':'failed','error':e.output[-1000:] if e.output else str(e)})
    print(json.dumps({'results':results},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
