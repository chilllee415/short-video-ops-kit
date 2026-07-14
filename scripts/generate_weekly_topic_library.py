#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "examples" / "topic-candidates.template.json"
HTML_PATH = ROOT / "examples" / "topic-candidates.html"


SCORE_KEYS = ("pain", "frequency", "demo", "payment", "productization")
SCORE_LABELS = {
    "pain": "痛感",
    "frequency": "频率",
    "demo": "演示",
    "payment": "付费",
    "productization": "产品化",
}


STYLE = r"""
:root{
  --bg:#0c1017;
  --bg2:#121826;
  --panel:#141b2b;
  --panel2:#1a2438;
  --line:#465884;
  --line-soft:#334263;
  --ink:#fbfcff;
  --muted:#c2cce0;
  --faint:#9ba8c4;
  --blue:#7fb0ff;
  --cyan:#69e0d0;
  --amber:#ffb86b;
  --coral:#ff7f6e;
  --green:#63d9a0;
  --glow:rgba(127,176,255,.24);
  --mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;
  --disp:"ZCOOL QingKe HuangYou","Noto Sans SC",sans-serif;
  --body:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  background:
    radial-gradient(980px 460px at 18% 12%, rgba(255,255,255,.11), transparent 58%),
    radial-gradient(760px 420px at 82% 18%, rgba(127,176,255,.12), transparent 60%),
    radial-gradient(720px 400px at 56% 78%, rgba(255,127,110,.09), transparent 62%),
    linear-gradient(180deg,#101624 0%, #0b1120 42%, #080d17 100%);
  color:var(--ink);
  font-family:var(--body);
  line-height:1.7;
  letter-spacing:0;
  -webkit-font-smoothing:antialiased;
}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    linear-gradient(90deg, rgba(148,164,195,.04) 1px, transparent 1px),
    linear-gradient(180deg, rgba(148,164,195,.04) 1px, transparent 1px);
  background-size:44px 44px;
  mask-image:linear-gradient(180deg,rgba(0,0,0,.9),rgba(0,0,0,.25) 60%,transparent);
}
body::after{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:1;
  background:
    linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,0) 28%),
    radial-gradient(56% 42% at 20% 14%, rgba(255,255,255,.06), transparent 72%),
    radial-gradient(44% 34% at 86% 20%, rgba(127,176,255,.08), transparent 70%);
}
button,summary{font:inherit}
.wrap{
  position:relative;z-index:1;width:min(1080px, calc(100% - 36px));margin:0 auto;padding:34px 0 60px;
}
.wrap::before{
  content:"";position:absolute;inset:20px -10px 20px -10px;z-index:-1;pointer-events:none;
  border:1px solid rgba(255,255,255,.07);border-radius:28px;
  box-shadow:0 0 0 1px rgba(127,176,255,.06), 0 0 36px rgba(127,176,255,.05);
}
.masthead{
  border:1px solid var(--line);
  border-radius:18px;
  background:linear-gradient(160deg, rgba(29,39,62,.78), rgba(13,19,32,.68));
  backdrop-filter:blur(22px) saturate(130%);
  -webkit-backdrop-filter:blur(22px) saturate(130%);
  box-shadow:0 24px 60px rgba(2,6,16,.5), inset 0 1px 0 rgba(255,255,255,.11);
  overflow:hidden;
  position:relative;
}
.masthead::before{
  content:"";position:absolute;inset:-30% auto auto -10%;width:58%;height:180%;
  background:linear-gradient(100deg, transparent 10%, rgba(255,255,255,.06) 38%, transparent 62%);
  transform:rotate(8deg);
  animation:mastSweep 12s linear infinite;
  pointer-events:none;
}
@keyframes mastSweep{from{translate:-120% 0}to{translate:210% 0}}
.mast-top{
  position:relative;z-index:1;display:flex;justify-content:space-between;align-items:center;gap:14px;
  padding:13px 22px;border-bottom:1px solid var(--line-soft);
  font-family:var(--mono);font-size:12.5px;color:var(--muted);
}
.dots{display:flex;gap:7px}
.dots i{width:10px;height:10px;border-radius:50%;display:block}
.dots i:nth-child(1){background:#ff6b6b}.dots i:nth-child(2){background:#ffc44d}.dots i:nth-child(3){background:#42d392}
.path{display:flex;align-items:center;gap:10px;min-width:0;flex:1;white-space:nowrap}
.workflow-id{flex:0 0 auto;color:var(--muted)}
.top-meta{min-width:0;overflow:hidden;text-overflow:ellipsis;color:var(--faint);font-size:11.5px;letter-spacing:.02em}
.top-meta strong{color:var(--amber);font-weight:800}
.live{display:flex;align-items:center;gap:7px;color:var(--cyan)}
.live b{width:7px;height:7px;border-radius:50%;background:var(--green);animation:pulse 1.6s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(66,211,146,.5)}55%{box-shadow:0 0 0 7px rgba(66,211,146,0)}}
.mast-body{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1.18fr) minmax(320px,.82fr);gap:24px;padding:28px 30px 30px}
.mast-side{display:grid;gap:14px;align-content:start}
.identity-card{
  display:grid;grid-template-columns:92px minmax(0,1fr);gap:16px;align-items:center;
  padding:18px;border-radius:20px;border:1px solid rgba(127,176,255,.26);
  background:linear-gradient(135deg, rgba(255,255,255,.16), rgba(127,176,255,.10)),rgba(16,23,38,.54);
  backdrop-filter:blur(18px) saturate(125%);
  -webkit-backdrop-filter:blur(18px) saturate(125%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.1), 0 18px 32px rgba(0,0,0,.2);
}
.identity-card img{width:92px;height:92px;border-radius:22px;display:block;object-fit:cover;border:1px solid rgba(244,247,251,.14);box-shadow:0 12px 28px rgba(0,0,0,.26)}
.identity-card .meta{display:flex;flex-direction:column;gap:6px;min-width:0}
.identity-card .label{font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;color:var(--cyan);text-transform:uppercase}
.identity-card .name{font-size:28px;line-height:1.1;font-weight:800;color:var(--ink)}
.identity-card .role{font-family:var(--mono);font-size:13px;letter-spacing:.16em;color:var(--muted)}
.identity-card .tagline{font-size:12.5px;color:var(--faint);line-height:1.6}
.eyebrow{
  font-family:var(--mono);font-size:11.5px;font-weight:600;letter-spacing:.22em;
  color:var(--cyan);text-transform:uppercase;margin-bottom:12px;
}
h1{
  font-family:var(--body);font-weight:900;
  font-size:clamp(34px,5vw,52px);line-height:1.12;letter-spacing:.01em;
  text-wrap:balance;overflow-wrap:anywhere;text-shadow:0 2px 18px rgba(127,176,255,.1);
}
h1 em{display:inline-block;margin-top:10px;font-family:var(--disp);font-style:normal;font-weight:400;letter-spacing:.06em;color:var(--blue);text-shadow:0 0 18px rgba(127,176,255,.16);max-width:100%;overflow-wrap:anywhere}
.mobile-break{display:none}
.mast-sub{color:var(--muted);margin-top:12px;max-width:48ch;font-size:14.5px}
.position-brief{
  margin-top:16px;border:1px solid rgba(105,224,208,.34);border-left:4px solid var(--cyan);
  border-radius:13px;padding:15px 17px;background:rgba(16,30,42,.46);
}
.position-brief .pb-label{
  font-family:var(--mono);font-size:10.5px;letter-spacing:.18em;color:var(--cyan);text-transform:uppercase;
}
.position-brief .pb-main{font-size:18px;font-weight:800;line-height:1.5;margin-top:6px}
.position-brief .pb-sub{font-size:12.5px;color:var(--muted);line-height:1.65;margin-top:7px}
.term{
  border:1px solid var(--line);border-radius:16px;background:#0b1220;
  font-family:var(--mono);font-size:12.5px;line-height:1.9;
  padding:16px 18px;align-self:center;min-height:172px;
  background:linear-gradient(180deg, rgba(17,24,39,.82), rgba(11,18,32,.72));
  backdrop-filter:blur(16px) saturate(120%);
  -webkit-backdrop-filter:blur(16px) saturate(120%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08), 0 16px 28px rgba(0,0,0,.18);
  position:relative;overflow:hidden;
}
.term .t-title{color:var(--faint);font-size:11px;letter-spacing:.14em;margin-bottom:8px;text-transform:uppercase}
.term .row{opacity:0;transform:translateY(4px);transition:opacity .35s,transform .35s;color:#d7e1f4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.term .row.on{opacity:1;transform:none}
.term .ts{color:#aab7d2}.term .ok{color:var(--green);font-weight:600}.term .hl{color:var(--amber)}
.caret{display:inline-block;width:8px;height:14px;background:var(--cyan);vertical-align:-2px;animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:14px}
.kpi{
  border:1px solid var(--line);border-radius:14px;padding:16px 16px 14px;
  background:linear-gradient(170deg, rgba(26,36,57,.74), rgba(13,18,30,.64));
  backdrop-filter:blur(16px) saturate(125%);
  -webkit-backdrop-filter:blur(16px) saturate(125%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.09);
  transition:transform .28s ease, box-shadow .28s ease, border-color .28s ease;
}
.kpi:hover{transform:translateY(-4px);box-shadow:inset 0 1px 0 rgba(255,255,255,.03),0 16px 28px rgba(0,0,0,.18);border-color:rgba(127,176,255,.32)}
.kpi .k-label{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:6px}
.kpi .k-val{font-family:var(--mono);font-weight:800;font-size:clamp(20px,2.6vw,27px);margin-top:6px;letter-spacing:-.01em}
.kpi .k-sub{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:4px}
.kpi .up{color:var(--green)}
.kpi.warn{border-color:rgba(255,184,107,.52);background:linear-gradient(170deg, rgba(66,41,27,.56), rgba(13,18,30,.94));position:relative;overflow:hidden}
.kpi.warn::after{content:"";position:absolute;inset:0;border-radius:14px;box-shadow:inset 0 0 34px rgba(242,166,90,.12);pointer-events:none}
.kpi.warn .k-val{color:var(--amber)}
.tag-warn{font-family:var(--mono);font-size:10px;font-weight:600;color:#1a1206;background:var(--amber);border-radius:5px;padding:1px 6px;letter-spacing:.06em}
section{margin-top:54px}
.sec-head{position:relative;display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--line-soft);padding-bottom:14px;margin-bottom:24px}
.sec-head::after{content:"";position:absolute;left:0;bottom:-1px;width:168px;height:1px;background:linear-gradient(90deg,var(--cyan),rgba(127,176,255,.72),transparent)}
.sec-no{
  font-family:var(--mono);font-weight:800;font-size:13px;color:var(--cyan);
  border:1px solid rgba(105,224,208,.34);border-radius:8px;padding:4px 10px;background:rgba(105,224,208,.08);
  letter-spacing:.08em;flex:0 0 auto;box-shadow:inset 0 1px 0 rgba(255,255,255,.08);
}
.sec-head h2{font-family:var(--disp);font-weight:400;font-size:clamp(24px,3.4vw,32px);letter-spacing:.02em;background:linear-gradient(90deg,var(--ink),rgba(127,176,255,.92));-webkit-background-clip:text;background-clip:text}
.sec-head .sec-q{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--faint);letter-spacing:.06em}
.sec-title{display:flex;align-items:baseline;gap:12px;min-width:0}
.sec-title .sec-desc{font-family:var(--mono);font-size:12px;color:var(--faint);letter-spacing:.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sec-actions{margin-left:auto;display:flex;align-items:center;gap:10px}
.reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.reveal.on{opacity:1;transform:none}
.stage-track{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:20px}
.stage{border:1px solid var(--line);border-radius:12px;padding:13px 15px;background:rgba(14,20,33,.78);color:var(--faint);font-size:13px;position:relative}
.stage .s-name{font-weight:700;color:var(--muted);font-size:14.5px}
.stage .s-desc{font-size:12px;margin-top:3px}
.stage.done::after{content:"✓";position:absolute;top:10px;right:12px;color:var(--green);font-family:var(--mono);font-size:12px}
.stage.now{border-color:rgba(127,176,255,.56);background:linear-gradient(170deg, rgba(32,48,82,.58), rgba(14,20,33,.96));box-shadow:0 0 0 1px rgba(127,176,255,.14), 0 14px 34px rgba(11,19,39,.28)}
.stage.now .s-name{color:var(--ink)}
.stage.now::before{content:"当前";position:absolute;top:-9px;right:10px;font-family:var(--mono);font-size:10px;font-weight:600;color:#081322;background:var(--blue);border-radius:5px;padding:1px 7px;letter-spacing:.1em}
.verdict{
  border:1px solid rgba(127,176,255,.32);border-left:4px solid var(--blue);
  border-radius:12px;padding:18px 22px;background:rgba(20,30,50,.62);
  font-size:15.5px;
}
.verdict b{color:var(--blue)}
.verdict .v-tag{font-family:var(--mono);font-size:11px;letter-spacing:.18em;color:var(--cyan);display:block;margin-bottom:6px}
.grid-2{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:14px;margin-top:14px}
.card{
  border:1px solid var(--line);border-radius:14px;padding:20px 22px;
  background:linear-gradient(170deg, rgba(25,35,55,.72), rgba(13,18,30,.62));
  backdrop-filter:blur(16px) saturate(125%);
  -webkit-backdrop-filter:blur(16px) saturate(125%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.09);
}
.card h3{font-size:15px;font-weight:700;display:flex;align-items:center;gap:8px}
.card h3 .dot{width:8px;height:8px;border-radius:2px;background:var(--cyan);display:inline-block;flex:0 0 auto}
.card .c-sub{font-size:13px;color:var(--muted);margin-top:3px}
.bars{margin-top:16px;display:grid;gap:13px}
.bar-row .b-top{display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:5px}
.bar-row .b-top .n{font-family:var(--mono);font-weight:600;color:var(--ink);font-size:12px}
.bar{height:9px;border-radius:6px;background:#0a0f1c;border:1px solid var(--line-soft);overflow:hidden}
.bar i{display:block;height:100%;width:0;border-radius:6px;transition:width 1.1s cubic-bezier(.2,.7,.2,1)}
.bar i.c1{background:linear-gradient(90deg,#69e0d0,#7fb0ff)}.bar i.c2{background:#6d7d9d}.bar i.c3{background:#53627d}.bar i.c4{background:#36445e}
.bench{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}
.bench .b-card{
  border:1px solid var(--line);border-radius:13px;padding:17px 18px;
  background:linear-gradient(180deg, rgba(20,29,45,.68), rgba(13,18,30,.58));position:relative;
  backdrop-filter:blur(14px) saturate(120%);
  -webkit-backdrop-filter:blur(14px) saturate(120%);
  overflow:hidden;
}
.bench .b-card::after{content:"";position:absolute;inset:auto 0 0 0;height:2px;background:linear-gradient(90deg,var(--cyan),var(--blue),transparent 88%);opacity:.7}
.bench .b-card .idx{font-family:var(--mono);font-size:11px;color:var(--cyan);letter-spacing:.14em}
.bench .b-card .b-name{font-weight:700;font-size:14.5px;margin-top:7px}
.bench .b-card .b-why{font-size:12.5px;color:var(--muted);margin-top:6px}
.bench .b-card .b-tag{display:inline-block;margin-top:11px;font-family:var(--mono);font-size:10.5px;color:var(--blue);border:1px solid rgba(108,158,255,.4);border-radius:5px;padding:2px 8px;letter-spacing:.06em}
.mini-tags{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}
.mini-tags span,.pill{
  font-family:var(--mono);font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:5px;padding:2px 8px;background:rgba(20,28,44,.72);
}
.mini-tags .hot,.pill.hot{color:var(--cyan);border-color:rgba(105,224,208,.42)}
.pool-toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.tool-btn{
  display:inline-flex;align-items:center;gap:7px;min-height:34px;
  border:1px solid rgba(105,224,208,.34);border-radius:10px;
  padding:6px 11px;background:rgba(13,18,30,.74);
  color:var(--ink);cursor:pointer;font-family:var(--mono);font-size:12px;font-weight:800;letter-spacing:.02em;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08);
  transition:transform .22s ease, border-color .22s ease, background .22s ease;
}
.tool-btn:hover{transform:translateY(-2px);border-color:rgba(105,224,208,.62);background:linear-gradient(90deg, rgba(105,224,208,.16), rgba(127,176,255,.12))}
.tool-btn:active{transform:translateY(0) scale(.98)}
.tool-btn .btn-mark{width:18px;height:18px;border:1px solid rgba(105,224,208,.34);border-radius:6px;display:grid;place-items:center;color:var(--cyan);line-height:1}
.topic-list{display:grid;gap:12px}
.topic-item{
  border:1px solid var(--line);border-radius:14px;
  background:linear-gradient(170deg, rgba(25,35,55,.72), rgba(13,18,30,.62));
  backdrop-filter:blur(16px) saturate(125%);
  -webkit-backdrop-filter:blur(16px) saturate(125%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.09);
  overflow:hidden;
  transition:border-color .24s ease, box-shadow .24s ease, transform .24s ease;
}
.topic-item:hover{border-color:rgba(127,176,255,.36);transform:translateY(-1px)}
.topic-item[open]{border-color:rgba(105,224,208,.38);box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 20px 34px rgba(0,0,0,.18)}
.topic-item summary{
  list-style:none;cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) 86px;
  gap:16px;padding:18px 20px;align-items:center;
}
.topic-item summary::-webkit-details-marker{display:none}
.summary-main h3{font-size:18px;line-height:1.45;font-weight:800;letter-spacing:0}
.summary-main p{font-size:13px;color:var(--muted);line-height:1.55;margin-top:7px}
.topic-meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:9px}
.priority,.meta-chip{
  font-family:var(--mono);font-size:11px;border:1px solid var(--line);border-radius:999px;padding:3px 8px;color:var(--muted);background:rgba(20,28,44,.72);
}
.priority{color:#081322;background:var(--green);border-color:transparent;font-weight:800}
.priority-b .priority{background:var(--amber)}.priority-c .priority{background:#8ea0bd}
.summary-side{
  width:78px;height:78px;border-radius:16px;display:grid;place-items:center;text-align:center;
  border:1px solid rgba(127,176,255,.36);background:#0b1220;
}
.summary-side strong{font-family:var(--mono);font-size:26px;line-height:1;color:var(--ink)}
.summary-side span{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:-14px}
.topic-detail{border-top:1px solid var(--line-soft);padding:18px 20px 20px;background:rgba(8,13,23,.34)}
.topic-detail-grid{display:grid;grid-template-columns:minmax(270px,.72fr) minmax(0,1.28fr);gap:12px;align-items:stretch}
.score-panel,.scene-panel{
  border:1px solid var(--line);border-radius:13px;padding:15px;
  background:linear-gradient(180deg, rgba(20,29,45,.68), rgba(13,18,30,.58));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06);
}
.score-panel h4,.scene-panel h4{font-size:14px;margin-bottom:10px}
.score-radar{display:grid;grid-template-columns:1fr;gap:10px;align-items:center;margin-top:2px}
.radar-svg{width:100%;max-width:258px;justify-self:center;overflow:visible}
.radar-grid{fill:none;stroke:rgba(127,176,255,.24);stroke-width:1}
.radar-grid.outer{stroke:rgba(105,224,208,.42)}
.radar-axis{stroke:rgba(194,204,224,.22);stroke-width:1}
.radar-area{
  fill:rgba(105,224,208,.24);stroke:var(--cyan);stroke-width:2;
  filter:drop-shadow(0 10px 18px rgba(105,224,208,.12));
  transform-origin:center;transform-box:fill-box;animation:radarIn .62s cubic-bezier(.16,1,.3,1) both;
}
.radar-point{fill:var(--cyan);stroke:#0b1220;stroke-width:2}
.radar-label{font-family:var(--mono);font-size:10.5px;fill:var(--muted);letter-spacing:.06em}
.radar-center{font-family:var(--mono);font-weight:800;font-size:25px;fill:var(--ink);text-anchor:middle}
.radar-center-sub{font-family:var(--mono);font-size:10px;fill:var(--faint);text-anchor:middle;letter-spacing:.12em}
.radar-legend{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}
.radar-legend-row{
  display:flex;align-items:center;justify-content:space-between;gap:8px;
  border:1px solid rgba(194,204,224,.14);border-radius:9px;padding:5px 8px;
  background:rgba(11,18,32,.46);font-family:var(--mono);font-size:11px;color:var(--muted);
}
.radar-legend-row b{color:var(--ink);font-size:11.5px}
.radar-legend-row.full{border-color:rgba(105,224,208,.34);background:rgba(105,224,208,.08)}
.radar-legend-row.mid b{color:var(--blue)}
@keyframes radarIn{from{opacity:.15;transform:scale(.82)}to{opacity:1;transform:scale(1)}}
.scene-rows{display:grid;gap:0;border-top:1px solid rgba(194,204,224,.12)}
.scene-row{
  display:grid;grid-template-columns:92px minmax(0,1fr);gap:14px;
  padding:10px 0;border-bottom:1px solid rgba(194,204,224,.11);
}
.scene-row b{font-family:var(--mono);font-size:11px;color:var(--cyan);letter-spacing:.08em}
.scene-row span{color:var(--muted);font-size:13.5px;line-height:1.62}
.evidence-strip{margin-top:12px;padding-top:12px;border-top:1px dashed rgba(194,204,224,.2)}
.evidence-strip b{display:block;font-size:13px;margin-bottom:8px}
.evidence-strip ul{margin:0;padding-left:18px;color:var(--muted);font-size:13px;line-height:1.7}
.gate-list{display:grid;gap:9px;margin-top:14px}
.gate-row{
  display:grid;grid-template-columns:78px minmax(0,1fr) 72px;gap:10px;align-items:center;
  border:1px solid var(--line);border-radius:12px;padding:11px 12px;
  background:linear-gradient(180deg, rgba(20,29,45,.68), rgba(13,18,30,.58));
}
.gate-row b{font-family:var(--mono);font-size:12px;color:var(--cyan);letter-spacing:.08em}
.gate-row span{font-size:12.5px;color:var(--muted);line-height:1.5}
.gate-row em{
  justify-self:end;font-style:normal;font-family:var(--mono);font-size:11px;color:var(--ink);
  border:1px solid rgba(105,224,208,.42);border-radius:999px;padding:3px 8px;background:rgba(105,224,208,.1);
}
.gate-total{
  margin-top:10px;border:1px solid rgba(255,184,107,.42);border-radius:12px;padding:10px 12px;
  color:var(--amber);font-family:var(--mono);font-size:12px;background:rgba(255,184,107,.08);
}
.timeline{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;margin-top:16px;border-radius:11px;overflow:hidden;border:1px solid var(--line)}
.tl-seg{padding:15px 15px 13px;background:rgba(20,28,44,.8);border-right:1px solid var(--line-soft)}
.tl-seg:last-child{border-right:0}
.tl-seg .t-time{font-family:var(--mono);font-size:11px;color:var(--cyan);letter-spacing:.06em}
.tl-seg .t-name{font-weight:700;font-size:14px;margin-top:5px}
.tl-seg .t-desc{font-size:12.5px;color:var(--muted);margin-top:4px}
.tl-seg.hot{background:linear-gradient(180deg, rgba(105,224,208,.16), rgba(20,28,44,.8))}
.source-strip{margin-top:16px;border-top:1px dashed var(--line-soft);padding-top:14px}
.source-strip .source-title{
  display:flex;align-items:center;gap:7px;
  font-family:var(--mono);font-size:11px;color:var(--cyan);letter-spacing:.12em;text-transform:uppercase;
}
.source-lines{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:10px}
.source-line{
  display:grid;grid-template-columns:38px minmax(0,1fr);gap:10px;align-items:start;
  border:1px solid var(--line);border-radius:12px;padding:10px;
  background:linear-gradient(180deg, rgba(20,29,45,.56), rgba(13,18,30,.5));
  font-size:12.5px;color:var(--muted);line-height:1.55;min-width:0;
}
.source-icon{
  width:38px;height:38px;border-radius:11px;display:grid;place-items:center;overflow:hidden;
  border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);
  box-shadow:0 8px 18px rgba(0,0,0,.18);
}
.source-icon img{width:100%;height:100%;display:block;object-fit:cover}
.source-copy{min-width:0}
.source-copy b{display:block;font-family:var(--mono);font-size:11.5px;color:var(--ink);letter-spacing:.04em;margin-bottom:2px}
.source-copy span{display:block}
footer{
  margin-top:60px;border-top:1px solid var(--line-soft);padding-top:26px;
  display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;
}
footer .f-left{font-family:var(--mono);font-size:12.5px;color:var(--muted);line-height:2}
.cta{
  font-size:15px;font-weight:700;border:1px solid rgba(105,224,208,.36);border-radius:999px;
  padding:11px 22px;background:linear-gradient(90deg, rgba(105,224,208,.12), rgba(127,176,255,.12));
  box-shadow:0 14px 28px rgba(0,0,0,.14);
}
.cta span{color:var(--cyan)}
@media (max-width:980px){
  .mast-body,.grid-2{grid-template-columns:1fr}
  .mast-side{order:-1}
  .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
  .kpis .kpi:last-child{grid-column:span 2}
  .bench,.bench.source,.topic-detail-grid{grid-template-columns:1fr}
  .gate-row{grid-template-columns:72px minmax(0,1fr)}
  .gate-row em{justify-self:start;grid-column:2}
  .source-lines{grid-template-columns:1fr}
  .stage-track,.timeline{grid-template-columns:repeat(2,minmax(0,1fr))}
  .tl-seg:nth-child(2){border-right:0}
  .sec-head .sec-q{display:none}
  .sec-title .sec-desc{display:none}
}
@media (max-width:560px){
  .wrap{width:min(100% - 24px,1080px);padding-top:22px}
  .mast-top{align-items:flex-start;flex-direction:column}
  .path{align-items:flex-start;flex-direction:column;gap:4px;white-space:normal}
  .top-meta{white-space:normal;line-height:1.5}
  .mast-body{padding:22px 18px}
  .identity-card{grid-template-columns:68px minmax(0,1fr);padding:14px}
  .identity-card img{width:68px;height:68px;border-radius:16px}
  .identity-card .name{font-size:22px}
  .identity-card .role{font-size:11px;letter-spacing:.12em}
  h1{font-size:30px;line-height:1.16}
  h1 em{display:block;font-size:28px;line-height:1.18;word-break:break-all}
  .mobile-break{display:block}
  .mast-sub{font-size:13.5px;max-width:100%;overflow-wrap:anywhere}
  .position-brief .pb-main{font-size:16px}
  .sec-head{align-items:flex-start;gap:10px;flex-wrap:wrap}
  .sec-title{flex:1 1 auto}
  .sec-actions{width:100%;margin-left:0}
  .pool-toolbar .tool-btn{flex:1;justify-content:center}
  .kpis,.stage-track,.timeline{grid-template-columns:1fr}
  .gate-row{grid-template-columns:1fr}
  .gate-row em{grid-column:auto}
  .source-line{grid-template-columns:34px minmax(0,1fr);padding:9px}
  .source-icon{width:34px;height:34px;border-radius:10px}
  .kpis .kpi:last-child{grid-column:auto}
  .topic-item summary{grid-template-columns:1fr}
  .summary-side{width:100%;height:auto;padding:11px;display:flex;gap:8px;justify-content:center}
  .summary-side span{margin-top:0}
  .radar-svg{max-width:232px}
  .radar-legend{grid-template-columns:repeat(2,minmax(0,1fr))}
  .scene-row{grid-template-columns:1fr;gap:4px;padding:9px 0}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important}
  .reveal,.term .row{opacity:1;transform:none}
}
"""


SCRIPT = r"""
(function(){
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var rows = document.querySelectorAll('#term .row');
  if(reduced){ rows.forEach(function(r){ r.classList.add('on'); }); }
  else{
    rows.forEach(function(r,i){ setTimeout(function(){ r.classList.add('on'); }, 500 + i*520); });
  }

  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){
        e.target.classList.add('on');
        activate(e.target);
        io.unobserve(e.target);
      }
    });
  },{threshold:.18});
  document.querySelectorAll('.reveal').forEach(function(el){ io.observe(el); });

  document.querySelectorAll('[data-action]').forEach(function(button){
    button.addEventListener('click', function(){
      var shouldOpen = button.dataset.action === 'open';
      document.querySelectorAll('.topic-item').forEach(function(item){
        item.open = shouldOpen;
      });
    });
  });

  function activate(scope){
    scope.querySelectorAll('.count').forEach(function(el){
      if(el.dataset.done) return; el.dataset.done = 1;
      var to = parseFloat(el.dataset.to), dec = parseInt(el.dataset.dec||'0',10);
      if(reduced){ el.textContent = to.toFixed(dec); return; }
      var t0 = null, dur = 1300;
      function step(t){
        if(!t0) t0 = t;
        var p = Math.min((t-t0)/dur,1);
        p = 1-Math.pow(1-p,3);
        el.textContent = (to*p).toFixed(dec);
        if(p<1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
    scope.querySelectorAll('[data-w]').forEach(function(b){
      requestAnimationFrame(function(){ b.style.width = b.dataset.w + '%'; });
    });
  }

  activate(document.querySelector('.kpis') || document.body);
})();
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=False)


def read_data() -> dict:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{DATA_PATH} must be a JSON object")
    return data


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def default_data_path() -> Path:
    workspace = os.environ.get("SHORT_VIDEO_OPS_WORKSPACE")
    if workspace:
        candidate = Path(workspace) / "archive" / "legacy-topics" / "topic-candidates.legacy.json"
        if candidate.exists():
            return candidate
    return ROOT / "examples" / "topic-candidates.template.json"


def default_html_path() -> Path:
    workspace = os.environ.get("SHORT_VIDEO_OPS_WORKSPACE")
    if workspace:
        return Path(workspace) / "archive" / "legacy-pages" / "选题库-每周场景雷达.html"
    return ROOT / "examples" / "topic-candidates.html"


def topic_score(topic: dict) -> int:
    scores = topic.get("score") or {}
    if not isinstance(scores, dict):
        return 0
    return sum(int(scores.get(key, 0) or 0) for key in SCORE_KEYS) * 4


def priority_class(priority: object) -> str:
    return {
        "A": "priority-a",
        "B": "priority-b",
        "C": "priority-c",
    }.get(str(priority).upper(), "priority-c")


def topic_counts(data: dict) -> dict[str, int]:
    counts = {"A": 0, "B": 0, "C": 0}
    for topic in data.get("topics", []):
        key = str(topic.get("priority", "C")).upper()
        counts[key] = counts.get(key, 0) + 1
    return counts


def content_ratio_value(data: dict, label: str, fallback: str = "0%") -> str:
    ratio = (data.get("weekly_strategy") or {}).get("content_ratio") or {}
    return str(ratio.get(label, fallback)).replace("%", "")


def chips(items: list[object], hot_first: bool = False) -> str:
    spans = []
    for index, item in enumerate(items):
        klass = ' class="hot"' if hot_first and index == 0 else ""
        spans.append(f"<span{klass}>{esc(item)}</span>")
    return '<div class="mini-tags">' + "".join(spans) + "</div>"


def source_lines(data: dict) -> str:
    icons = {
        "小红书": "./assets/platform-icons/xiaohongshu.png",
        "B站": "./assets/platform-icons/bilibili.png",
        "抖音评论/私信": "./assets/platform-icons/douyin.png",
        "招聘JD/岗位说明": "./assets/platform-icons/boss-zhipin.png",
    }
    lines = []
    for item in data.get("source_mix", []):
        source = str(item.get("source", ""))
        lines.append(
            f"""
            <div class="source-line">
              <span class="source-icon"><img src="{esc(icons.get(source, "./assets/platform-icons/xiaohongshu.png"))}" alt="{esc(source)} 图标" loading="lazy"></span>
              <span class="source-copy">
                <b>{esc(source)}</b>
                <span>{esc(item.get("use", ""))}</span>
              </span>
            </div>
            """
        )
    return "\n".join(lines)


def scoring_gate_rows(data: dict) -> str:
    thresholds = {
        "pain": "5分优先",
        "frequency": "4分+",
        "demo": "4分+",
        "payment": "3分+",
        "productization": "4分+",
    }
    rows = []
    for item in data.get("scoring_rubric", []):
        key = str(item.get("key", ""))
        rows.append(
            f"""
            <div class="gate-row">
              <b>{esc(item.get("label", ""))}</b>
              <span>{esc(item.get("question", ""))}</span>
              <em>{esc(thresholds.get(key, "观察"))}</em>
            </div>
            """
        )
    rows.append('<div class="gate-total">总分门禁：80+ 才进入本周优先脚本池</div>')
    return "\n".join(rows)


def ratio_timeline(data: dict) -> str:
    ratio = (data.get("weekly_strategy") or {}).get("content_ratio") or {}
    labels = list(ratio.items())
    rows = []
    for index, (label, value) in enumerate(labels[:4]):
        klass = " hot" if index == 0 else ""
        rows.append(
            f"""
            <div class="tl-seg{klass}">
              <div class="t-time">{esc(value)}</div>
              <div class="t-name">{esc(label)}</div>
              <div class="t-desc">本周内容配比</div>
            </div>
            """
        )
    return "\n".join(rows)


def radar_point(cx: float, cy: float, radius: float, index: int, total: int) -> tuple[float, float]:
    angle = -math.pi / 2 + (math.tau * index / total)
    return cx + math.cos(angle) * radius, cy + math.sin(angle) * radius


def svg_points(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def score_radar(topic: dict) -> str:
    scores = topic.get("score") or {}
    cx, cy, radius = 120.0, 108.0, 70.0
    label_radius = 94.0
    total = len(SCORE_KEYS)
    values = [max(0, min(5, int(scores.get(key, 0) or 0))) for key in SCORE_KEYS]

    grids = []
    for level in range(1, 6):
        klass = "radar-grid outer" if level == 5 else "radar-grid"
        points = [radar_point(cx, cy, radius * level / 5, index, total) for index in range(total)]
        grids.append(f'<polygon class="{klass}" points="{svg_points(points)}"></polygon>')

    axes = []
    labels = []
    data_points = []
    points = []
    for index, (key, value) in enumerate(zip(SCORE_KEYS, values)):
        axis_end = radar_point(cx, cy, radius, index, total)
        axes.append(f'<line class="radar-axis" x1="{cx:.1f}" y1="{cy:.1f}" x2="{axis_end[0]:.1f}" y2="{axis_end[1]:.1f}"></line>')

        label_x, label_y = radar_point(cx, cy, label_radius, index, total)
        if label_x < cx - 8:
            anchor = "end"
        elif label_x > cx + 8:
            anchor = "start"
        else:
            anchor = "middle"
        labels.append(f'<text class="radar-label" x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="{anchor}" dominant-baseline="middle">{SCORE_LABELS[key]}</text>')

        data_point = radar_point(cx, cy, radius * value / 5, index, total)
        points.append(data_point)
        data_points.append(f'<circle class="radar-point" cx="{data_point[0]:.1f}" cy="{data_point[1]:.1f}" r="3.6"></circle>')

    legend_rows = []
    for key, value in zip(SCORE_KEYS, values):
        klass = " full" if value >= 5 else " mid" if value >= 4 else ""
        legend_rows.append(
            f'<div class="radar-legend-row{klass}"><span>{SCORE_LABELS[key]}</span><b>{value}/5</b></div>'
        )

    score = topic_score(topic)
    label = " / ".join(f"{SCORE_LABELS[key]} {value}/5" for key, value in zip(SCORE_KEYS, values))
    return f"""
    <div class="score-radar" aria-label="{esc(label)}">
      <svg class="radar-svg" viewBox="0 0 240 216" role="img" aria-label="评分雷达">
        <g>{"".join(grids)}</g>
        <g>{"".join(axes)}</g>
        <polygon class="radar-area" points="{svg_points(points)}"></polygon>
        <g>{"".join(data_points)}</g>
        <text class="radar-center" x="{cx:.1f}" y="{cy + 2:.1f}">{score}</text>
        <text class="radar-center-sub" x="{cx:.1f}" y="{cy + 19:.1f}">SCORE</text>
        <g>{"".join(labels)}</g>
      </svg>
      <div class="radar-legend">{"".join(legend_rows)}</div>
    </div>
    """


def scene_row(label: str, text: object) -> str:
    return f'<div class="scene-row"><b>{esc(label)}</b><span>{esc(text)}</span></div>'


def evidence_list(topic: dict) -> str:
    evidence = topic.get("evidence") or []
    if not evidence:
        return "<li>暂无补充备注</li>"
    return "".join(f"<li>{esc(item)}</li>" for item in evidence[:4])


def topic_list(data: dict) -> str:
    topics = sorted(data.get("topics", []), key=lambda item: (-topic_score(item), item.get("id", "")))
    rows = []
    for index, topic in enumerate(topics):
        priority = str(topic.get("priority", "C")).upper()
        score = topic_score(topic)
        open_attr = " open" if index == 0 else ""
        rows.append(
            f"""
            <details class="topic-item {priority_class(priority)} reveal"{open_attr}>
              <summary>
                <div class="summary-main">
                  <div class="topic-meta">
                    <span class="priority">{esc(priority)}</span>
                    <span class="meta-chip">{esc(topic.get("id", ""))}</span>
                    <span class="meta-chip">{esc(topic.get("role", ""))}</span>
                  </div>
                  <h3>{esc(topic.get("hook", ""))}</h3>
                  <p>{esc(topic.get("scene", ""))}</p>
                </div>
                <div class="summary-side">
                  <strong>{score}</strong>
                  <span>score</span>
                </div>
              </summary>
              <div class="topic-detail">
                <div class="topic-detail-grid">
                  <div class="score-panel">
                    <h4>评分雷达</h4>
                    {score_radar(topic)}
                  </div>
                  <div class="scene-panel">
                    <h4>场景拆解</h4>
                    <div class="scene-rows">
                      {scene_row("用户痛点", topic.get("pain", ""))}
                      {scene_row("重复动作", topic.get("repeated_action", ""))}
                      {scene_row("AI接入点", topic.get("ai_entry", ""))}
                      {scene_row("可见结果", topic.get("visible_result", ""))}
                      {scene_row("拍法", topic.get("video_angle", ""))}
                      {scene_row("CTA", topic.get("cta", ""))}
                    </div>
                    <div class="evidence-strip">
                      <b>证据 / 备注</b>
                      <ul>{evidence_list(topic)}</ul>
                    </div>
                  </div>
                </div>
              </div>
            </details>
            """
        )
    return "\n".join(rows)


def action_cards(data: dict) -> str:
    cards = []
    action_label = str(data.get("action_label") or "本周执行")
    for index, action in enumerate(data.get("weekly_actions") or [], start=1):
        cards.append(
            f"""
            <div class="b-card">
              <div class="idx">ACT-{index:02d}</div>
              <div class="b-name">{esc(action)}</div>
              <span class="b-tag">{esc(action_label)}</span>
            </div>
            """
        )
    return "\n".join(cards)


def account_positioning(data: dict) -> dict:
    value = data.get("account_positioning") or {}
    return value if isinstance(value, dict) else {}


def pos_text(positioning: dict, key: str, fallback: str = "") -> str:
    value = positioning.get(key, fallback)
    if isinstance(value, list):
        return " / ".join(str(item) for item in value)
    return str(value or fallback)


def render(data: dict) -> str:
    strategy = data.get("weekly_strategy") or {}
    positioning = account_positioning(data)
    operator = data.get("operator_profile") or {}
    counts = topic_counts(data)
    focus_roles = strategy.get("focus_roles") or []
    avoid = strategy.get("avoid") or []
    positioning_audience = positioning.get("audience") or focus_roles
    topics = data.get("topics", [])
    total_topics = len(topics)
    top_topic = max(topics, key=topic_score) if topics else {}
    top_score = topic_score(top_topic) if top_topic else 0
    account_handle = str(data.get("account_handle") or "@ client_account")
    operator_name = str(operator.get("name") or "Commercial Ops Workflow")
    operator_label = str(operator.get("label") or "Workflow Profile")
    operator_role = str(operator.get("role") or "Short Video Growth System")
    operator_tagline = str(operator.get("tagline") or "用数据确认策略，用场景生成选题。")
    operator_avatar = str(operator.get("avatar") or "./assets/operator-avatar.svg")
    positioning_label = str(positioning.get("label") or "账号定位")
    log_positioning = str(data.get("strategy_name") or "策略确认后锁定")
    workflow_slug = str(data.get("workflow_slug") or "topic-candidates")
    action_section_title = str(data.get("action_section_title") or "本周执行")
    action_subtitle = str(data.get("action_subtitle") or "进入脚本前，继续保持成果前置和诊断型 CTA。")
    footer_label = str(data.get("footer_label") or "每周场景选题雷达")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(data.get("title", "每周真实场景选题雷达"))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=ZCOOL+QingKe+HuangYou&family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">

  <header class="masthead">
    <div class="mast-top">
      <div class="dots"><i></i><i></i><i></i></div>
      <div class="path">
        <span class="workflow-id">~/workflow/{esc(workflow_slug)} -- {esc(data.get("week", ""))}</span>
        <span class="top-meta">{esc(account_handle)} · {esc(data.get("date_range", ""))} · 生成 {esc(data.get("generated_at", ""))} · 门禁 <strong>80+</strong></span>
      </div>
      <div class="live"><b></b>TOPIC&nbsp;PIPELINE</div>
    </div>
    <div class="mast-body">
      <div>
        <div class="eyebrow">Commercial Topic Workbench · Scenario Radar</div>
        <h1>{esc(data.get("title", ""))}<br><em>账号定位 / 选题策略 /<br class="mobile-break"> 选题池</em></h1>
        <div class="position-brief">
          <div class="pb-label">{esc(positioning_label)}</div>
          <div class="pb-main">{esc(pos_text(positioning, "one_liner", data.get("positioning", "")))}</div>
          <div class="pb-sub">{esc(pos_text(positioning, "content_promise", data.get("subtitle", "")))}</div>
        </div>
        <p class="mast-sub">{esc(data.get("weekly_question", ""))}</p>
      </div>
      <div class="mast-side">
        <div class="identity-card" aria-label="工作流信息">
          <img src="{esc(operator_avatar)}" alt="工作流标识">
          <div class="meta">
            <span class="label">{esc(operator_label)}</span>
            <span class="name">{esc(operator_name)}</span>
            <span class="role">{esc(operator_role)}</span>
            <span class="tagline">{esc(operator_tagline)}</span>
          </div>
        </div>
        <div class="term" id="term">
          <div class="t-title">topic-candidates.log</div>
          <div class="row"><span class="ts">[定位]</span> {esc(log_positioning)} <span class="ok">locked</span></div>
          <div class="row"><span class="ts">[选题]</span> 候选 {total_topics} 条 · A级 {counts.get("A", 0)} 条 <span class="ok">ready</span></div>
          <div class="row"><span class="ts">[人群]</span> 重点角色 {len(positioning_audience)} 类 · 从重复动作出发 <span class="ok">ready</span></div>
          <div class="row"><span class="ts">[策略]</span> 结果演示 {esc(content_ratio_value(data, "短入口结果演示", "40"))}% · 评分门禁 80+ <span class="ok">ready</span></div>
          <div class="row"><span class="ts">[优先]</span> 最高评分 {top_score} · <span class="hl">{esc(top_topic.get("hook", "从真实场景里找选题"))}</span> <span class="caret"></span></div>
        </div>
      </div>
    </div>
  </header>

  <section id="strategy">
    <div class="sec-head reveal">
      <span class="sec-no">PART 01</span>
      <h2>选题策略</h2>
      <span class="sec-q">// 用同一把尺子筛选</span>
    </div>

    <div class="grid-2">
      <div class="card reveal">
        <h3><span class="dot"></span>内容配比</h3>
        <div class="c-sub">下周制作节奏按这个比例分配。</div>
        <div class="timeline">{ratio_timeline(data)}</div>
        <div class="source-strip">
          <div class="source-title">research sources</div>
          <div class="source-lines">{source_lines(data)}</div>
        </div>
      </div>
      <div class="card reveal">
        <h3><span class="dot"></span>评分门禁</h3>
        <div class="c-sub">每项同时给判断问题和通过标准，看完就知道该不该进脚本池。</div>
        <div class="gate-list">{scoring_gate_rows(data)}</div>
      </div>
    </div>

  </section>

  <section id="pool">
    <div class="sec-head reveal pool-head">
      <span class="sec-no">PART 02</span>
      <div class="sec-title">
        <h2>选题池</h2>
        <span class="sec-desc">// 默认展开最高分，点开细看脚本结构</span>
      </div>
      <div class="sec-actions pool-toolbar" aria-label="选题池操作">
        <button class="tool-btn" type="button" data-action="open"><span class="btn-mark" aria-hidden="true">+</span>全部展开</button>
        <button class="tool-btn" type="button" data-action="close"><span class="btn-mark" aria-hidden="true">-</span>全部收起</button>
      </div>
    </div>

    <div class="topic-list">{topic_list(data)}</div>
  </section>

  <section id="action">
    <div class="sec-head reveal">
      <span class="sec-no">PART 03</span>
      <h2>{esc(action_section_title)}</h2>
      <span class="sec-q">// 从选题进入拍摄</span>
    </div>

    <div class="card reveal">
      <h3><span class="dot"></span>执行清单</h3>
      <div class="c-sub">{esc(action_subtitle)}</div>
      <div class="bench">{action_cards(data)}</div>
    </div>
  </section>

  <footer class="reveal">
    <div class="f-left">
      {esc(footer_label)} · 随输入数据覆盖更新<br>
      数据源 {esc(display_path(DATA_PATH))} · 输出 {esc(display_path(HTML_PATH))}
    </div>
    <div class="cta">今日动作：<span>先从A级选题里挑2条短入口和1条场景拆解。</span></div>
  </footer>

</div>

<script>{SCRIPT}</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the weekly topic radar HTML page.")
    parser.add_argument("--input", type=Path, default=default_data_path())
    parser.add_argument("--output", type=Path, default=default_html_path())
    args = parser.parse_args()

    global DATA_PATH, HTML_PATH
    DATA_PATH = args.input.resolve()
    HTML_PATH = args.output.resolve()

    data = read_data()
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(render(data), encoding="utf-8")
    print(f"updated: {HTML_PATH}")
    print(f"source: {DATA_PATH}")


if __name__ == "__main__":
    main()
