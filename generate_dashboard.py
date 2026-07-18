#!/usr/bin/env python3
"""
generate_dashboard.py
Regenerates the Job Agent Dashboard HTML from applications_log.json.
Run after each agent execution to keep the dashboard current.

Usage:
  python generate_dashboard.py
  python generate_dashboard.py --output C:/path/to/custom.html
"""

import json
import sys
import os
import argparse
from datetime import datetime
from collections import Counter

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH   = os.path.join(SCRIPT_DIR, "applications_log.json")
OUT_PATH   = os.path.join(SCRIPT_DIR, "logs", "dashboard_data.html")

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--output", default=OUT_PATH, help="Output HTML file path")
parser.add_argument("--log", default=LOG_PATH, help="Path to applications_log.json")
args = parser.parse_args()

# ── Load data ─────────────────────────────────────────────────────────────────
if not os.path.exists(args.log):
    print(f"ERROR: Log file not found: {args.log}")
    sys.exit(1)

with open(args.log, encoding="utf-8") as f:
    raw = json.load(f)

# Normalize & sort (newest date + highest priority first)
rows = []
for e in raw:
    rows.append({
        "job_id":           e.get("job_id", ""),
        "title":            e.get("title", ""),
        "company":          e.get("company", ""),
        "location":         e.get("location", ""),
        "url":              e.get("url", ""),
        "source":           e.get("source", ""),
        "status":           e.get("status", "resume_ready"),
        "applied_date":     e.get("applied_date", ""),
        "priority_label":   e.get("priority_label", ""),
        "priority_score":   e.get("priority_score") or 0,
        "match_score":      e.get("match_score") or 0,
        "salary_offered":   e.get("salary_offered", ""),
        "salary_submitted": e.get("salary_submitted", ""),
        "easy_apply":       bool(e.get("easy_apply", False)),
        "run_id":           e.get("run_id", ""),
        "resume_file":      e.get("resume_file", ""),
        "description_snippet": (e.get("description_snippet") or "")[:200],
    })

rows.sort(key=lambda x: (x["applied_date"], x["priority_score"]), reverse=True)
data_json = json.dumps(rows, ensure_ascii=False)

# ── Stats ─────────────────────────────────────────────────────────────────────
total   = len(rows)
applied = sum(1 for r in rows if r["status"] == "applied")
ready   = sum(1 for r in rows if r["status"] == "resume_ready")
dates   = sorted(set(r["applied_date"] for r in rows if r["applied_date"]), reverse=True)
last_run = dates[0] if dates else "N/A"

statuses_vals = sorted(set(r["status"] for r in rows if r["status"]))
source_vals   = sorted(set(r["source"] for r in rows if r["source"]))
date_vals     = sorted(set(r["applied_date"] for r in rows if r["applied_date"]), reverse=True)

status_opts = "".join(f'<option value="{s}">{s}</option>' for s in statuses_vals)
source_opts = "".join(f'<option value="{s}">{s}</option>' for s in source_vals)
date_opts   = "".join(f'<option value="{d}">{d}</option>' for d in date_vals)

generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job Agent Dashboard</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridjs@5.0.2/dist/theme/mermaid.min.css" integrity="sha384-jZvDSsmGB9oGGT/4l9bHXGoAv1OxvG/cFmSo0dZaSqmBgvQTKDBFAMftlXTmMbNW" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/gridjs@5.0.2/dist/gridjs.umd.js" integrity="sha384-/XXDzxe4FsGiAe50i/u9pY/Vy/uX654MHB1xoc1BJNnH1WXHhqHga9g3q5tF4gj7" crossorigin="anonymous"></script>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fa; color: #1a1a2e; font-size: 13px; }}
  .header {{ background: linear-gradient(135deg, #0a2342 0%, #1565c0 100%); color: white; padding: 16px 20px; }}
  .header h1 {{ font-size: 18px; font-weight: 700; margin-bottom: 2px; }}
  .header .subtitle {{ font-size: 11px; opacity: 0.75; }}
  .stats-row {{ display: flex; gap: 10px; padding: 14px 20px; background: white; border-bottom: 1px solid #e0e4ea; flex-wrap: wrap; }}
  .stat-card {{ flex: 1; min-width: 100px; background: #f8faff; border: 1px solid #dce4f5; border-radius: 8px; padding: 10px 14px; text-align: center; }}
  .stat-card .val {{ font-size: 26px; font-weight: 800; line-height: 1; }}
  .stat-card .lbl {{ font-size: 10px; color: #666; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat-card.applied {{ border-color: #43a047; background: #f1f8f1; }}
  .stat-card.applied .val {{ color: #2e7d32; }}
  .stat-card.ready {{ border-color: #fb8c00; background: #fff8f0; }}
  .stat-card.ready .val {{ color: #e65100; }}
  .stat-card.total .val {{ color: #1565c0; }}
  .stat-card.date .val {{ font-size: 14px; font-weight: 700; color: #555; }}
  .filters {{ display: flex; gap: 8px; padding: 12px 20px; background: white; border-bottom: 1px solid #e0e4ea; flex-wrap: wrap; align-items: center; }}
  .filters label {{ font-size: 11px; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: 0.4px; margin-right: 2px; }}
  .search-wrap {{ display: flex; align-items: center; gap: 6px; flex: 1; min-width: 200px; }}
  .search-wrap input {{ flex: 1; padding: 6px 10px; border: 1px solid #d0d7e6; border-radius: 6px; font-size: 12px; outline: none; }}
  .search-wrap input:focus {{ border-color: #1565c0; box-shadow: 0 0 0 2px rgba(21,101,192,0.15); }}
  .filter-group {{ display: flex; align-items: center; gap: 5px; }}
  select {{ padding: 6px 8px; border: 1px solid #d0d7e6; border-radius: 6px; font-size: 12px; background: white; cursor: pointer; outline: none; color: #333; }}
  select:focus {{ border-color: #1565c0; }}
  .btn-reset {{ padding: 6px 12px; background: #f0f3f8; border: 1px solid #d0d7e6; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; color: #555; }}
  .btn-reset:hover {{ background: #e3e8f0; }}
  .table-wrap {{ padding: 16px 20px; }}
  .gridjs-wrapper {{ border: 1px solid #dce4f5; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  th.gridjs-th {{ background: #e8eef9; color: #1a2e5c; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; padding: 8px 10px; border-bottom: 2px solid #c5d1ec; white-space: nowrap; }}
  td.gridjs-td {{ padding: 7px 10px; border-bottom: 1px solid #edf0f7; font-size: 12px; vertical-align: middle; }}
  tr.gridjs-tr:hover td {{ background: #f0f5ff; }}
  .gridjs-pagination {{ padding: 10px 14px; background: #f8faff; border-top: 1px solid #e0e4ea; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; letter-spacing: 0.3px; text-transform: uppercase; white-space: nowrap; }}
  .badge-applied {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
  .badge-ready {{ background: #fff3cd; color: #856404; border: 1px solid #ffc107; }}
  .badge-ea {{ background: #cce5ff; color: #004085; border: 1px solid #b8daff; font-size: 9px; }}
  .chip {{ display: inline-block; padding: 2px 7px; border-radius: 8px; font-size: 10px; font-weight: 600; white-space: nowrap; }}
  .chip-dice {{ background: #fff0e6; color: #bf5700; }}
  .chip-linkedin {{ background: #e6f0ff; color: #0a66c2; }}
  .chip-indeed {{ background: #e6ffe6; color: #0d5916; }}
  .chip-zip {{ background: #f5e6ff; color: #6a0080; }}
  .chip-other {{ background: #f0f0f0; color: #555; }}
  .job-link {{ color: #1565c0; text-decoration: none; font-weight: 600; }}
  .job-link:hover {{ text-decoration: underline; }}
  .company-name {{ font-weight: 600; color: #1a1a2e; }}
  .score {{ font-weight: 700; color: #555; }}
  .score-high {{ color: #2e7d32; font-weight: 700; }}
  .score-med {{ color: #e65100; font-weight: 700; }}
  .no-data {{ color: #bbb; font-style: italic; }}
  .updated-note {{ font-size: 10px; color: #999; padding: 6px 20px 12px; text-align: right; }}
</style>
</head>
<body>

<div class="header">
  <h1>🤖 Job Agent Dashboard — Adalberto Silveira Napoles</h1>
  <div class="subtitle">Senior Java Full-Stack Engineer · Hialeah, FL · 18+ años experiencia</div>
</div>

<div class="stats-row">
  <div class="stat-card total"><div class="val">{total}</div><div class="lbl">Total</div></div>
  <div class="stat-card applied"><div class="val">{applied}</div><div class="lbl">✅ Applied</div></div>
  <div class="stat-card ready"><div class="val">{ready}</div><div class="lbl">📄 Resume Ready</div></div>
  <div class="stat-card date"><div class="val">{last_run}</div><div class="lbl">Último run</div></div>
  <div class="stat-card"><div class="val" id="filtered-count">{total}</div><div class="lbl">Visible</div></div>
</div>

<div class="filters">
  <div class="search-wrap">
    <label>🔍</label>
    <input type="text" id="search-input" placeholder="Buscar compañía, título, ubicación, prioridad..." />
  </div>
  <div class="filter-group">
    <label>Estado</label>
    <select id="filter-status">
      <option value="">Todos</option>
      {status_opts}
    </select>
  </div>
  <div class="filter-group">
    <label>Fuente</label>
    <select id="filter-source">
      <option value="">Todas</option>
      {source_opts}
    </select>
  </div>
  <div class="filter-group">
    <label>Fecha</label>
    <select id="filter-date">
      <option value="">Todas</option>
      {date_opts}
    </select>
  </div>
  <div class="filter-group">
    <label>Easy Apply</label>
    <select id="filter-ea">
      <option value="">Todos</option>
      <option value="true">Solo Easy Apply</option>
      <option value="false">Sin Easy Apply</option>
    </select>
  </div>
  <button class="btn-reset" onclick="resetFilters()">↺ Limpiar</button>
</div>

<div class="table-wrap">
  <div id="grid-container"></div>
</div>
<div class="updated-note">Generado: {generated_at} · {total} registros · applications_log.json</div>

<script>
const APPS_DATA = {data_json};

function statusBadge(s) {{
  if (s === 'applied') return '<span class="badge badge-applied">✅ Applied</span>';
  if (s === 'resume_ready') return '<span class="badge badge-ready">📄 Resume Ready</span>';
  return '<span class="badge" style="background:#eee;color:#666">' + s + '</span>';
}}
function sourceChip(s) {{
  const sl = (s||'').toLowerCase();
  let cls = 'chip-other';
  if (sl.includes('dice')) cls = 'chip-dice';
  else if (sl.includes('linkedin')) cls = 'chip-linkedin';
  else if (sl.includes('indeed')) cls = 'chip-indeed';
  else if (sl.includes('zip')) cls = 'chip-zip';
  return '<span class="chip ' + cls + '">' + (s||'') + '</span>';
}}
function scoreHtml(v) {{
  if (!v && v !== 0) return '<span class="no-data">—</span>';
  const cls = v >= 50 ? 'score-high' : v >= 20 ? 'score-med' : 'score';
  return '<span class="' + cls + '">' + v + '%</span>';
}}
function eaBadge(v) {{
  return v ? '<span class="badge badge-ea">⚡ EA</span>' : '<span class="no-data">—</span>';
}}
function salaryShort(s) {{
  if (!s || s === '--' || s === 'Depends on Experience') return '<span class="no-data">N/A</span>';
  return s;
}}

let grid = null;

function getFiltered() {{
  const q   = (document.getElementById('search-input').value || '').toLowerCase();
  const st  = document.getElementById('filter-status').value;
  const src = document.getElementById('filter-source').value;
  const dt  = document.getElementById('filter-date').value;
  const ea  = document.getElementById('filter-ea').value;
  return APPS_DATA.filter(r => {{
    if (q && !((r.company||'').toLowerCase().includes(q) ||
               (r.title||'').toLowerCase().includes(q) ||
               (r.location||'').toLowerCase().includes(q) ||
               (r.priority_label||'').toLowerCase().includes(q))) return false;
    if (st  && r.status !== st) return false;
    if (src && r.source !== src) return false;
    if (dt  && r.applied_date !== dt) return false;
    if (ea === 'true'  && !r.easy_apply) return false;
    if (ea === 'false' &&  r.easy_apply) return false;
    return true;
  }});
}}

function toRows(items) {{
  return items.map((r, i) => [
    i + 1,
    r.applied_date || '',
    r.company || '',
    r.title || '',
    r.location || '',
    r.source || '',
    r.status || '',
    r.salary_offered || '',
    r.match_score,
    r.priority_score,
    r.easy_apply,
    r.url || ''
  ]);
}}

function renderGrid(data) {{
  document.getElementById('filtered-count').textContent = data.length;
  if (grid) {{ grid.updateConfig({{ data: toRows(data) }}).forceRender(); return; }}
  grid = new gridjs.Grid({{
    columns: [
      {{ name: '#', width: '40px' }},
      {{ name: 'Fecha', width: '90px', sort: true }},
      {{ name: 'Compañía', width: '150px', sort: true,
         formatter: c => gridjs.html('<span class="company-name">' + c + '</span>') }},
      {{ name: 'Título', width: '200px', sort: true }},
      {{ name: 'Ubicación', width: '130px' }},
      {{ name: 'Fuente', width: '110px', sort: true,
         formatter: c => gridjs.html(sourceChip(c)) }},
      {{ name: 'Estado', width: '120px', sort: true,
         formatter: c => gridjs.html(statusBadge(c)) }},
      {{ name: 'Salario Ofrecido', width: '155px',
         formatter: c => gridjs.html(salaryShort(c)) }},
      {{ name: 'Match%', width: '65px', sort: true,
         formatter: c => gridjs.html(scoreHtml(c)) }},
      {{ name: 'Pri.', width: '55px', sort: true,
         formatter: c => gridjs.html('<span class="score">' + (c||0) + '</span>') }},
      {{ name: 'EA', width: '50px',
         formatter: c => gridjs.html(eaBadge(c)) }},
      {{ name: 'Link', width: '55px', sort: false,
         formatter: c => gridjs.html(c ? '<a class="job-link" href="' + c + '" target="_blank">Ver →</a>' : '') }}
    ],
    data: toRows(data),
    sort: true,
    pagination: {{ limit: 25, summary: true }},
    search: false,
    language: {{
      pagination: {{ previous: '‹', next: '›', showing: 'Mostrando', results: () => 'resultados', of: 'de', to: 'a' }}
    }}
  }}).render(document.getElementById('grid-container'));
}}

function applyFilters() {{ renderGrid(getFiltered()); }}
function resetFilters() {{
  document.getElementById('search-input').value = '';
  document.getElementById('filter-status').value = '';
  document.getElementById('filter-source').value = '';
  document.getElementById('filter-date').value = '';
  document.getElementById('filter-ea').value = '';
  applyFilters();
}}

document.getElementById('search-input').addEventListener('input', applyFilters);
document.getElementById('filter-status').addEventListener('change', applyFilters);
document.getElementById('filter-source').addEventListener('change', applyFilters);
document.getElementById('filter-date').addEventListener('change', applyFilters);
document.getElementById('filter-ea').addEventListener('change', applyFilters);

renderGrid(APPS_DATA);
</script>
</body>
</html>"""

os.makedirs(os.path.dirname(args.output), exist_ok=True)
with open(args.output, "w", encoding="utf-8") as f:
    f.write(html)

print(f"ok: Dashboard generated → {args.output}")
print(f"    {total} entries | {applied} applied | {ready} resume_ready | last_run={last_run}")
