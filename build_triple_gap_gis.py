#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Triple Synchronized GIS Dashboard with Gap Analysis for Chiang Mai Water Master Plan
Features:
  - 3 Synchronized Maps: Risk (5 Pillars), Budget (65-70), and Gap Analysis
  - Toggle Village Pins Button (default OFF to keep overview clean & comfortable)
  - Crisp District Boundaries (คมชัด แยกชัดเจน 25 อำเภอ พร้อมป้ายชื่ออำเภอ)
  - Google Maps Base Layers with Roadmap & Terrain
"""

import json
import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

# Load GeoJSON datasets
with open('chiangmai_districts_gis.geojson', 'r', encoding='utf-8') as f:
    districts_geojson = json.load(f)

with open('chiangmai_subdistricts_gis.geojson', 'r', encoding='utf-8') as f:
    subdistricts_geojson = json.load(f)

with open('chiangmai_villages_gis.geojson', 'r', encoding='utf-8') as f:
    villages_geojson = json.load(f)

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    dash_data = json.load(f)

# Load subdistrict gap CSV to enrich subdistrict properties
df_sub = pd.read_csv('data_clean_csv/05_สรุปรายตำบล_GapAnalysis.csv', encoding='utf-8')

def get_subdistrict_gap_status(high_risk, budget):
    if high_risk >= 10 and budget < 40:
        return '🚨 เสี่ยงสูงวิกฤติ - งบประมาณไม่เพียงพอ'
    elif high_risk >= 8 and budget >= 40:
        return '⚠️ เสี่ยงสูง - ได้รับงบประมาณต่อเนื่อง'
    elif high_risk >= 3 and budget < 20:
        return '🟡 เสี่ยงปานกลาง - ควรเพิ่มงบประมาณ'
    elif high_risk == 0 and budget >= 50:
        return '🔵 งบประมาณสูง - ความเสี่ยงต่ำ (โครงการโครงสร้างพื้นฐานหลัก)'
    else:
        return '🟢 สมดุลตามเกณฑ์'

sub_gap_dict = {}
for _, row in df_sub.iterrows():
    key = f"{row['อำเภอ']}_{row['ตำบล']}"
    high_total = int(row['เสี่ยงสูง_รวมทุกด้าน'])
    budget_total = float(row['งบประมาณรวม (ล้านบาท)'])
    gap_stat = get_subdistrict_gap_status(high_total, budget_total)
    sub_gap_dict[key] = {
        'villages': int(row['จำนวนหมู่บ้าน']),
        'high_risk_total': high_total,
        'high_p1': int(row['เสี่ยงสูง_ด1']),
        'high_p2': int(row['เสี่ยงสูง_ด2']),
        'high_p3': int(row['เสี่ยงสูง_ด3']),
        'high_p4': int(row['เสี่ยงสูง_ด4']),
        'high_p5': int(row['เสี่ยงสูง_ด5']),
        'total_projects': int(row['จำนวนโครงการ']),
        'total_budget': budget_total,
        'budget_p1': float(row['งบ_ด1 (ล้านบาท)']),
        'budget_p2': float(row['งบ_ด2 (ล้านบาท)']),
        'budget_p3': float(row['งบ_ด3 (ล้านบาท)']),
        'budget_p4': float(row['งบ_ด4 (ล้านบาท)']),
        'budget_p5': float(row['งบ_ด5 (ล้านบาท)']),
        'gap_status': gap_stat
    }

for feat in subdistricts_geojson['features']:
    props = feat['properties']
    key = f"{props.get('amp_th')}_{props.get('tam_th')}"
    if key in sub_gap_dict:
        props.update(sub_gap_dict[key])

districts_json_str = json.dumps(districts_geojson, ensure_ascii=False)
subdistricts_json_str = json.dumps(subdistricts_geojson, ensure_ascii=False)
villages_json_str = json.dumps(villages_geojson, ensure_ascii=False)
dash_data_json_str = json.dumps(dash_data, ensure_ascii=False)

html_template = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ระบบสารสนเทศภูมิศาสตร์ 3 แผนที่คู่ขนาน (ความเสี่ยง vs งบประมาณ vs Gap Analysis) จ.เชียงใหม่</title>
  
  <!-- Google Fonts & Material Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
  
  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  
  <style>
    :root {
      --primary: #1a73e8;
      --primary-dark: #1557b0;
      --bg: #f8fafd;
      --card-bg: #ffffff;
      --text-main: #202124;
      --text-sub: #5f6368;
      --border: #dadce0;
      --shadow: 0 2px 6px rgba(60,64,67, 0.12);
      --shadow-lg: 0 8px 24px rgba(60,64,67, 0.22);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Prompt', 'Google Sans', sans-serif; }
    body { background: var(--bg); color: var(--text-main); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

    /* Remove focus outlines & rectangles */
    path.leaflet-interactive:focus { outline: none !important; }
    svg:focus { outline: none !important; }
    .leaflet-container:focus { outline: none !important; }

    /* Top Google Navbar */
    header {
      background: #ffffff;
      border-bottom: 1px solid var(--border);
      padding: 8px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 1000;
      box-shadow: 0 1px 3px rgba(60,64,67, 0.08);
      flex-shrink: 0;
      gap: 12px;
    }
    .header-brand { display: flex; align-items: center; gap: 10px; }
    .brand-icon {
      width: 38px; height: 38px;
      background: linear-gradient(135deg, #1a73e8, #7c3aed);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      color: #fff; font-size: 20px;
      flex-shrink: 0;
    }
    .brand-title { font-size: 0.98rem; font-weight: 700; color: #1a73e8; line-height: 1.2; }
    .brand-sub { font-size: 0.73rem; color: var(--text-sub); }

    /* Page Switcher Dropdown & Nav */
    .nav-switcher {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .nav-dropdown-btn {
      background: #f1f3f4;
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 5px 12px;
      font-size: 0.78rem;
      font-weight: 600;
      color: #202124;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .nav-dropdown-btn:hover {
      background: #e8f0fe;
      color: #1a73e8;
      border-color: #aecbfa;
    }
    .nav-dropdown-menu {
      position: absolute;
      top: 50px;
      left: 20px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: var(--shadow-lg);
      padding: 8px 0;
      min-width: 280px;
      z-index: 2000;
      display: none;
    }
    .nav-dropdown-menu.show {
      display: block;
    }
    .nav-menu-item {
      padding: 8px 16px;
      font-size: 0.8rem;
      color: #3c4043;
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      transition: background 0.15s;
    }
    .nav-menu-item:hover {
      background: #f1f3f4;
      color: #1a73e8;
    }
    .nav-menu-item.active {
      background: #e8f0fe;
      color: #1a73e8;
      font-weight: 700;
    }

    /* Layout View Switcher Pills */
    .layout-switcher {
      display: flex;
      align-items: center;
      background: #f1f3f4;
      padding: 3px;
      border-radius: 20px;
      border: 1px solid var(--border);
      gap: 2px;
    }
    .layout-btn {
      border: none;
      background: none;
      padding: 4px 10px;
      border-radius: 16px;
      font-size: 0.74rem;
      font-weight: 600;
      color: #5f6368;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .layout-btn.active {
      background: #ffffff;
      color: #1a73e8;
      box-shadow: 0 1px 3px rgba(60,64,67, 0.2);
    }

    .header-kpis { display: flex; align-items: center; gap: 8px; }
    .kpi-chip {
      background: #f8f9fa;
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 16px;
      font-size: 0.74rem;
      display: flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }
    .kpi-chip strong { color: #1a73e8; font-weight: 700; }
    .kpi-chip.chip-gap-crisis strong { color: #d93025; }

    /* Filter Action Bar (Top) */
    .filter-bar {
      background: #ffffff;
      border-bottom: 1px solid var(--border);
      padding: 6px 20px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      z-index: 900;
      flex-shrink: 0;
    }
    .filter-group { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
    
    .search-input-wrap {
      position: relative;
      width: 180px;
    }
    .search-input-wrap input {
      width: 100%;
      height: 32px;
      padding: 0 10px 0 30px;
      border: 1px solid var(--border);
      border-radius: 16px;
      font-size: 0.78rem;
      background: #f8f9fa;
      outline: none;
      transition: all 0.2s;
    }
    .search-input-wrap input:focus {
      background: #ffffff;
      border-color: var(--primary);
      box-shadow: 0 0 0 2px rgba(26,115,232,0.2);
    }
    .search-input-wrap .search-icon {
      position: absolute;
      left: 8px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 16px;
      color: #5f6368;
      pointer-events: none;
    }

    .filter-select {
      height: 32px;
      padding: 0 22px 0 8px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: #f8f9fa;
      font-size: 0.76rem;
      color: var(--text-main);
      outline: none;
      cursor: pointer;
      appearance: none;
      background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%235f6368'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
      background-repeat: no-repeat;
      background-position: right 6px center;
      background-size: 14px;
      transition: border-color 0.2s;
    }
    .filter-select:focus {
      border-color: var(--primary);
      background-color: #ffffff;
    }

    /* Toggle Village Pins Button */
    .btn-toggle-pins {
      height: 32px;
      padding: 0 12px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: #ffffff;
      color: #5f6368;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
    }
    .btn-toggle-pins:hover {
      background: #f1f3f4;
      color: #202124;
      border-color: #5f6368;
    }
    .btn-toggle-pins.active {
      background: #e8f0fe;
      color: #1a73e8;
      border-color: #aecbfa;
      box-shadow: 0 1px 3px rgba(26,115,232,0.25);
    }

    .filter-btn-reset {
      height: 32px;
      padding: 0 12px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: #ffffff;
      color: #5f6368;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .filter-btn-reset:hover {
      background: #f1f3f4;
      color: #202124;
      border-color: #5f6368;
    }

    /* Main Triple Map Container */
    .map-main-wrapper {
      position: relative;
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      height: calc(100vh - 96px);
      overflow: hidden;
      background: #e5e3df;
      transition: grid-template-columns 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .map-box {
      position: relative;
      width: 100%;
      height: 100%;
      border-right: 2px solid #ffffff;
    }
    .map-box:last-child {
      border-right: none;
    }

    .leaflet-map {
      width: 100%;
      height: 100%;
      background: #e5e3df;
    }

    /* District Labels on Map */
    .district-label-card {
      background: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(0, 0, 0, 0.15);
      border-radius: 6px;
      padding: 2px 6px;
      font-size: 0.72rem;
      font-weight: 700;
      color: #1e293b;
      box-shadow: 0 1px 3px rgba(0,0,0,0.12);
      text-align: center;
      white-space: nowrap;
      pointer-events: none;
    }
    .district-sublabel {
      font-size: 0.62rem;
      font-weight: 500;
      color: #64748b;
    }

    /* Floating Map Headers / Badges */
    .map-header-badge {
      position: absolute;
      top: 12px;
      left: 12px;
      z-index: 800;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(0,0,0,0.12);
      border-radius: 8px;
      padding: 6px 12px;
      box-shadow: var(--shadow);
      pointer-events: none;
    }
    .badge-title { font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 6px; }
    .badge-sub { font-size: 0.68rem; color: var(--text-sub); margin-top: 2px; }

    .badge-risk .badge-title { color: #c5221f; }
    .badge-budget .badge-title { color: #1a73e8; }
    .badge-gap .badge-title { color: #7c3aed; }

    /* Map Legends (Bottom Right of each map) */
    .map-legend {
      position: absolute;
      bottom: 64px;
      right: 12px;
      z-index: 800;
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(6px);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 0.68rem;
      box-shadow: var(--shadow);
      max-width: 220px;
    }
    .legend-title { font-weight: 700; margin-bottom: 4px; color: #202124; }
    .legend-row { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
    .legend-color { width: 12px; height: 10px; border-radius: 2px; display: inline-block; flex-shrink: 0; }

    /* SMART FLOATING BOTTOM DOCK */
    .smart-dock {
      position: absolute;
      bottom: 12px;
      left: 50%;
      transform: translateX(-50%);
      width: min(94%, 960px);
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: var(--shadow-lg);
      z-index: 850;
      overflow: hidden;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .dock-summary-bar {
      padding: 8px 14px;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      cursor: pointer;
      user-select: none;
      flex-wrap: wrap;
    }
    .dock-title-group {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    
    /* Breadcrumbs navigation */
    .dock-breadcrumbs {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.84rem;
      font-weight: 700;
      color: #202124;
    }
    .bc-item {
      cursor: pointer;
      color: #1a73e8;
      border-radius: 4px;
      padding: 1px 4px;
      transition: background 0.15s;
    }
    .bc-item:hover {
      background: #e8f0fe;
      text-decoration: underline;
    }
    .bc-active {
      color: #202124;
      cursor: default;
    }
    .bc-separator {
      color: #80868b;
      font-size: 0.72rem;
    }

    .dock-stat-pill {
      background: #f1f3f4;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-weight: 600;
      color: #3c4043;
      white-space: nowrap;
    }
    .pill-score { background: #fef7e0; color: #b06000; border: 1px solid #fce8b2; }
    .pill-risk { background: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
    .pill-budget { background: #e8f0fe; color: #1967d2; border: 1px solid #aecbfa; }
    .pill-gap-red { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    .pill-gap-orange { background: #ffedd5; color: #9a3412; border: 1px solid #fdba74; }
    .pill-gap-yellow { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
    .pill-gap-blue { background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }
    .pill-gap-green { background: #dcfce7; color: #166534; border: 1px solid #86efac; }

    .dock-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-dock-home {
      background: #f1f3f4;
      color: #3c4043;
      border: 1px solid var(--border);
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .btn-dock-home:hover {
      background: #e8f0fe;
      color: #1a73e8;
    }
    .btn-toggle-expand {
      background: #1a73e8;
      color: #ffffff;
      border: none;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .btn-close-dock {
      background: none;
      border: none;
      color: #5f6368;
      cursor: pointer;
      padding: 2px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
    }
    .btn-close-dock:hover { background: #f1f3f4; }

    .dock-expanded-content {
      max-height: 0;
      overflow: hidden;
      background: #fafafa;
      transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      border-top: 1px solid #f1f3f4;
    }
    .smart-dock.expanded .dock-expanded-content {
      max-height: 380px;
      overflow-y: auto;
    }
    .dock-inner-padding {
      padding: 12px 16px;
    }

    /* FLOATING BACK TO OVERVIEW BUTTON (Top Center) */
    .floating-back-bar {
      position: absolute;
      top: 12px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 850;
      display: none;
    }
    .btn-floating-back {
      background: #ffffff;
      color: #1a73e8;
      border: 1px solid #aecbfa;
      border-radius: 20px;
      padding: 6px 16px;
      font-size: 0.78rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: var(--shadow-lg);
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .btn-floating-back:hover {
      background: #1a73e8;
      color: #ffffff;
    }

    /* Pulsing Beacon Animation */
    .pulsing-beacon {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: rgba(26, 115, 232, 0.85);
      border: 2px solid #ffffff;
      box-shadow: 0 0 10px rgba(26, 115, 232, 0.8);
      animation: pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }
    .pulsing-beacon-gap {
      background: rgba(124, 58, 237, 0.9);
      box-shadow: 0 0 10px rgba(124, 58, 237, 0.8);
    }
    @keyframes pulse-ring {
      0% { transform: scale(0.6); opacity: 1; }
      50% { transform: scale(1.4); opacity: 0.5; }
      100% { transform: scale(0.6); opacity: 1; }
    }

    /* Gap Matrix Table */
    .gap-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.74rem;
      background: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .gap-table th {
      background: #f1f3f4;
      color: #3c4043;
      padding: 6px 8px;
      text-align: left;
      font-weight: 600;
      border-bottom: 1px solid var(--border);
    }
    .gap-table td {
      padding: 6px 8px;
      border-bottom: 1px solid #f1f3f4;
      color: #202124;
    }
    .gap-table tr:hover td {
      background: #f8fafd;
    }

    /* Responsive */
    @media (max-width: 1024px) {
      .map-main-wrapper {
        grid-template-columns: 1fr;
        grid-template-rows: 1fr 1fr 1fr;
      }
      .map-box {
        border-right: none;
        border-bottom: 2px solid #ffffff;
      }
    }
  </style>
</head>
<body>

  <!-- Top Google Navbar -->
  <header>
    <div class="header-brand">
      <div class="brand-icon">
        <span class="material-symbols-outlined">balance</span>
      </div>
      <div>
        <div class="brand-title">ระบบวิเคราะห์ช่องว่าง 3 แผนที่คู่ขนาน (Triple Sync GIS)</div>
        <div class="brand-sub">เปรียบเทียบความเสี่ยง vs งบประมาณ vs Gap Analysis แผนแม่บทน้ำ จ.เชียงใหม่</div>
      </div>
    </div>

    <!-- Navigation Switcher Menu -->
    <div class="nav-switcher">
      <div style="position:relative;">
        <button class="nav-dropdown-btn" onclick="toggleNavDropdown(event)">
          <span class="material-symbols-outlined" style="font-size:16px; color:#1a73e8;">apps</span>
          <span>สลับหน้าแดชบอร์ด</span>
          <span class="material-symbols-outlined" style="font-size:14px;">arrow_drop_down</span>
        </button>
        <div class="nav-dropdown-menu" id="navDropdownMenu">
          <a href="index.html" class="nav-menu-item">
            <span class="material-symbols-outlined" style="color:#1a73e8;">map</span>
            <div>
              <div style="font-weight:600;">1. แผนที่คู่ขนาน (Dual GIS)</div>
              <div style="font-size:0.7rem; color:#5f6368;">เปรียบเทียบความเสี่ยง 5 มิติ vs งบประมาณ</div>
            </div>
          </a>
          <a href="ChiangMai_Water_Triple_Gap_GIS_Dashboard.html" class="nav-menu-item active">
            <span class="material-symbols-outlined" style="color:#7c3aed;">balance</span>
            <div>
              <div style="font-weight:700;">2. วิเคราะห์ช่องว่าง 3 แผนที่ (Triple Sync GIS)</div>
              <div style="font-size:0.7rem; color:#5f6368;">ความเสี่ยง vs งบประมาณ vs Gap Analysis (หน้านี้)</div>
            </div>
          </a>
          <a href="ChiangMai_Water_Dashboard.html" class="nav-menu-item">
            <span class="material-symbols-outlined" style="color:#059669;">analytics</span>
            <div>
              <div style="font-weight:600;">3. รายงานผู้บริหาร & สถิติภาพรวม</div>
              <div style="font-size:0.7rem; color:#5f6368;">Executive Overview & Summary Cards</div>
            </div>
          </a>
          <a href="ChiangMai_Flood_Household_GIS_Dashboard.html" class="nav-menu-item">
            <span class="material-symbols-outlined" style="color:#d97706;">home</span>
            <div>
              <div style="font-weight:600;">4. สำรวจครัวเรือนน้ำท่วม (Flood Survey)</div>
              <div style="font-size:0.7rem; color:#5f6368;">ข้อมูลระดับครัวเรือน 4,450 ครัวเรือน</div>
            </div>
          </a>
        </div>
      </div>

      <!-- Layout Switcher Pills -->
      <div class="layout-switcher">
        <button class="layout-btn active" id="btnLayoutTriple" onclick="setLayoutMode('triple')" title="แสดง 3 แผนที่พร้อมกัน">
          <span class="material-symbols-outlined" style="font-size:14px;">view_column</span> 3 แผนที่
        </button>
        <button class="layout-btn" id="btnLayoutRiskGap" onclick="setLayoutMode('risk-gap')" title="เปรียบเทียบ ความเสี่ยง vs Gap">
          <span class="material-symbols-outlined" style="font-size:14px;">view_agenda</span> เสี่ยง vs Gap
        </button>
        <button class="layout-btn" id="btnLayoutBudgetGap" onclick="setLayoutMode('budget-gap')" title="เปรียบเทียบ งบประมาณ vs Gap">
          <span class="material-symbols-outlined" style="font-size:14px;">view_agenda</span> งบ vs Gap
        </button>
        <button class="layout-btn" id="btnLayoutGapOnly" onclick="setLayoutMode('gap-only')" title="เจาะลึกเฉพาะ Gap Analysis เต็มจอ">
          <span class="material-symbols-outlined" style="font-size:14px;">fullscreen</span> เจาะลึก Gap
        </button>
      </div>
    </div>

    <!-- KPI Chips -->
    <div class="header-kpis">
      <div class="kpi-chip">💰 งบประมาณ: <strong>35,094.77 ลบ.</strong></div>
      <div class="kpi-chip">🚨 จุดเสี่ยงสูง: <strong>1,040 จุด</strong></div>
      <div class="kpi-chip chip-gap-crisis">⚡ Gap วิกฤติ: <strong>3 อำเภอ (สารภี/สันกำแพง/แม่อาย)</strong></div>
    </div>
  </header>

  <!-- Filter Action Bar (Top) -->
  <div class="filter-bar">
    <div class="filter-group">
      <!-- Search Input -->
      <div class="search-input-wrap">
        <span class="material-symbols-outlined search-icon">search</span>
        <input type="text" id="searchInput" placeholder="ค้นหา อำเภอ / ตำบล / หมู่บ้าน..." oninput="handleSearch(this.value)">
      </div>

      <!-- 3-Tier Drill-down Dropdowns -->
      <select class="filter-select" id="districtSelect" onchange="handleDistrictSelect(this.value)">
        <option value="all">📍 ทุกอำเภอ (25 อำเภอ)</option>
      </select>

      <select class="filter-select" id="subdistrictSelect" onchange="handleSubdistrictSelect(this.value)">
        <option value="all">🏘️ ทุกตำบล (204 ตำบล)</option>
      </select>

      <select class="filter-select" id="villageSelect" onchange="handleVillageSelect(this.value)">
        <option value="all">🏡 ทุกหมู่บ้าน (2,200 หมู่บ้าน)</option>
      </select>
    </div>

    <div class="filter-group">
      <!-- Gap Status Filter -->
      <select class="filter-select" id="gapStatusSelect" onchange="handleGapFilter(this.value)">
        <option value="all">⚖️ ทุกสถานะ Gap Analysis</option>
        <option value="🚨 เสี่ยงสูงวิกฤติ - งบประมาณไม่เพียงพอ">🚨 เสี่ยงสูงวิกฤติ - งบไม่พอ (18 ตำบล)</option>
        <option value="⚠️ เสี่ยงสูง - ได้รับงบประมาณต่อเนื่อง">⚠️ เสี่ยงสูง - งบต่อเนื่อง (37 ตำบล)</option>
        <option value="🟡 เสี่ยงปานกลาง - ควรเพิ่มงบประมาณ">🟡 เสี่ยงปานกลาง - ควรเพิ่มงบ (13 ตำบล)</option>
        <option value="🔵 งบประมาณสูง - ความเสี่ยงต่ำ (โครงการโครงสร้างพื้นฐานหลัก)">🔵 งบสูง - เสี่ยงต่ำ (57 ตำบล)</option>
        <option value="🟢 สมดุลตามเกณฑ์">🟢 สมดุลตามเกณฑ์ (79 ตำบล)</option>
      </select>

      <!-- Pillar Filter -->
      <select class="filter-select" id="pillarSelect" onchange="handlePillarSelect(this.value)">
        <option value="all">💧 แผนแม่บท 5 ด้าน (รวม)</option>
        <option value="1">💧 ด้าน 1: น้ำอุปโภคบริโภค</option>
        <option value="2">🌾 ด้าน 2: น้ำภาคเกษตร</option>
        <option value="3">🌊 ด้าน 3: น้ำท่วมและอุทกภัย</option>
        <option value="4">🧪 ด้าน 4: คุณภาพน้ำและการอนุรักษ์</option>
        <option value="5">🌲 ด้าน 5: ฟื้นฟูป่าต้นน้ำ</option>
      </select>

      <!-- Toggle Village Pins Button (Default: OFF) -->
      <button class="btn-toggle-pins" id="btnTogglePins" onclick="toggleVillagePins()" title="เปิด/ปิด การแสดงหมุด 2,200 หมู่บ้าน">
        <span class="material-symbols-outlined" style="font-size:16px;">pin_drop</span>
        <span id="txtTogglePins">แสดงหมุดหมู่บ้าน (ปิดอยู่)</span>
      </button>

      <!-- Reset Button -->
      <button class="filter-btn-reset" onclick="resetToOverview()" title="ล้างตัวกรองและกลับสู่ภาพรวม">
        <span class="material-symbols-outlined" style="font-size:16px;">refresh</span>
        <span>รีเซ็ต</span>
      </button>
    </div>
  </div>

  <!-- Main Triple Map Container -->
  <div class="map-main-wrapper" id="mapWrapper">

    <!-- MAP 1: RISK MAP (Left) -->
    <div class="map-box" id="boxRisk">
      <div id="map-risk" class="leaflet-map"></div>
      <div class="map-header-badge badge-risk">
        <div class="badge-title"><span class="material-symbols-outlined" style="font-size:16px;">warning</span> 1. แผนที่ความเสี่ยง 5 ด้าน</div>
        <div class="badge-sub">ระดับความรุนแรง 2,200 หมู่บ้าน</div>
      </div>
      <div class="map-legend">
        <div class="legend-title">ระดับความเสี่ยง</div>
        <div class="legend-row"><span class="legend-color" style="background:#ef4444;"></span> วิกฤติสูงมาก (12-15 คะแนน)</div>
        <div class="legend-row"><span class="legend-color" style="background:#f97316;"></span> เฝ้าระวังสูง (10-11 คะแนน)</div>
        <div class="legend-row"><span class="legend-color" style="background:#eab308;"></span> เฝ้าระวังปานกลาง (8-9 คะแนน)</div>
        <div class="legend-row"><span class="legend-color" style="background:#22c55e;"></span> เสี่ยงน้อย (5-7 คะแนน)</div>
      </div>
    </div>

    <!-- MAP 2: BUDGET MAP (Center) -->
    <div class="map-box" id="boxBudget">
      <div id="map-budget" class="leaflet-map"></div>
      <div class="map-header-badge badge-budget">
        <div class="badge-title"><span class="material-symbols-outlined" style="font-size:16px;">payments</span> 2. แผนที่จัดสรรงบประมาณ</div>
        <div class="badge-sub">งบแผนแม่บท 65-70 (35.09 พันลบ.)</div>
      </div>
      <div class="map-legend">
        <div class="legend-title">งบประมาณจัดสรร (ลบ.)</div>
        <div class="legend-row"><span class="legend-color" style="background:#0d47a1;"></span> สูงมาก (> 3,000 ลบ.)</div>
        <div class="legend-row"><span class="legend-color" style="background:#1976d2;"></span> สูง (1,500 - 3,000 ลบ.)</div>
        <div class="legend-row"><span class="legend-color" style="background:#42a5f5;"></span> ปานกลาง (800 - 1,500 ลบ.)</div>
        <div class="legend-row"><span class="legend-color" style="background:#90caf9;"></span> น้อย (400 - 800 ลบ.)</div>
        <div class="legend-row"><span class="legend-color" style="background:#e3f2fd;"></span> น้อยมาก (< 400 ลบ.)</div>
      </div>
    </div>

    <!-- MAP 3: GAP ANALYSIS MAP (Right) -->
    <div class="map-box" id="boxGap">
      <div id="map-gap" class="leaflet-map"></div>
      <div class="map-header-badge badge-gap">
        <div class="badge-title"><span class="material-symbols-outlined" style="font-size:16px;">balance</span> 3. แผนที่วิเคราะห์ช่องว่าง (Gap Analysis)</div>
        <div class="badge-sub">วิเคราะห์ความสอดคล้อง เสี่ยง vs งบประมาณ</div>
      </div>
      <div class="map-legend">
        <div class="legend-title">สถานะช่องว่าง (Gap Status)</div>
        <div class="legend-row"><span class="legend-color" style="background:#ef4444;"></span> 🚨 เสี่ยงสูงวิกฤติ - งบไม่พอ</div>
        <div class="legend-row"><span class="legend-color" style="background:#f97316;"></span> ⚠️ เสี่ยงสูง - งบต่อเนื่อง</div>
        <div class="legend-row"><span class="legend-color" style="background:#eab308;"></span> 🟡 เสี่ยงปานกลาง - ควรเพิ่มงบ</div>
        <div class="legend-row"><span class="legend-color" style="background:#3b82f6;"></span> 🔵 งบสูง - เสี่ยงต่ำ (โครงสร้างฯ)</div>
        <div class="legend-row"><span class="legend-color" style="background:#22c55e;"></span> 🟢 สมดุลตามเกณฑ์</div>
      </div>
    </div>

    <!-- FLOATING BACK TO OVERVIEW BUTTON (Top Center) -->
    <div class="floating-back-bar" id="floatingBackBar">
      <button class="btn-floating-back" onclick="resetToOverview()" title="ย้อนกลับไปดูภาพรวมทั้ง 25 อำเภอ">
        <span class="material-symbols-outlined" style="font-size:18px;">arrow_back</span>
        <span id="floatingBackText">ย้อนกลับภาพรวม จ.เชียงใหม่</span>
      </button>
    </div>

    <!-- SMART FLOATING BOTTOM DOCK -->
    <div class="smart-dock" id="smartDock">
      <div class="dock-summary-bar" onclick="toggleDockExpand()">
        <div class="dock-title-group" id="dockTitleGroup">
          <span class="material-symbols-outlined" style="color:#7c3aed; font-size:20px;">info</span>
          <div class="dock-breadcrumbs" id="dockBreadcrumbs">
            <span class="bc-active">📍 จ.เชียงใหม่ (ภาพรวม 25 อำเภอ)</span>
          </div>
          <span class="dock-stat-pill pill-gap-red" id="dockPillGap">🚨 Gap วิกฤติ 3 อำเภอ</span>
          <span class="dock-stat-pill pill-risk" id="dockPillRisk">🔴 เสี่ยงสูง 1,040 จุด</span>
          <span class="dock-stat-pill pill-budget" id="dockPillBudget">💰 35,094.77 ลบ. (6,312 โครงการ)</span>
        </div>
        <div class="dock-actions" onclick="event.stopPropagation()">
          <button class="btn-dock-home" onclick="resetToOverview()" title="กลับสู่ภาพรวมทั้ง 25 อำเภอ">
            <span class="material-symbols-outlined" style="font-size:14px;">restart_alt</span>
            <span>กลับภาพรวม</span>
          </button>
          <button class="btn-toggle-expand" id="btnDockExpand" onclick="toggleDockExpand()">
            <span class="material-symbols-outlined" style="font-size:16px;" id="expandIcon">expand_less</span>
            <span id="expandText">ดูตาราง Gap 5 มิติ</span>
          </button>
          <button class="btn-close-dock" onclick="closeDock()">
            <span class="material-symbols-outlined" style="font-size:16px;">close</span>
          </button>
        </div>
      </div>
      <div class="dock-expanded-content">
        <div class="dock-inner-padding" id="dockExpandedBody"></div>
      </div>
    </div>

  </div>

  <script>
    // Embedded GeoJSON Datasets
    const DISTRICTS_DATA = __DISTRICTS_DATA__;
    const SUBDISTRICTS_DATA = __SUBDISTRICTS_DATA__;
    const VILLAGES_DATA = __VILLAGES_DATA__;
    const SUMMARY_DATA = __SUMMARY_DATA__;

    let mapRisk, mapBudget, mapGap;
    let districtLayersRisk = {}, districtLayersBudget = {}, districtLayersGap = {};
    let subdistrictGroupRisk = null, subdistrictGroupBudget = null, subdistrictGroupGap = null;
    let villagePointsRisk = null, villagePointsBudget = null, villagePointsGap = null;
    
    let activePulseRisk = null, activePulseBudget = null, activePulseGap = null;
    let showVillages = false; // Default: OFF (Clean overview, no scary clusters)
    let isSyncing = false;
    let cmBounds;

    let selectedDistrict = 'all';
    let selectedSubdistrict = 'all';
    let selectedVillageId = 'all';
    let selectedGapFilter = 'all';
    let selectedPillar = 'all';
    let currentLayout = 'triple';

    window.addEventListener('DOMContentLoaded', () => {
      initMaps();
      populateDropdowns();
      renderAllLayers();
      resetToOverview();
    });

    function initMaps() {
      const cmCenter = [18.7883, 98.9853];
      const initialZoom = 9;
      const googleMapsUrl = 'https://mt1.google.com/vt/lyrs=m&hl=th&x={x}&y={y}&z={z}';

      // 1. Left Map: Risk
      mapRisk = L.map('map-risk', {
        center: cmCenter,
        zoom: initialZoom,
        zoomControl: false,
        boxZoom: false
      });
      L.tileLayer(googleMapsUrl, { maxZoom: 18, attribution: '© Google Maps' }).addTo(mapRisk);

      // 2. Center Map: Budget
      mapBudget = L.map('map-budget', {
        center: cmCenter,
        zoom: initialZoom,
        zoomControl: false,
        boxZoom: false
      });
      L.tileLayer(googleMapsUrl, { maxZoom: 18, attribution: '© Google Maps' }).addTo(mapBudget);

      // 3. Right Map: Gap
      mapGap = L.map('map-gap', {
        center: cmCenter,
        zoom: initialZoom,
        zoomControl: false,
        boxZoom: false
      });
      L.tileLayer(googleMapsUrl, { maxZoom: 18, attribution: '© Google Maps' }).addTo(mapGap);
      L.control.zoom({ position: 'topright' }).addTo(mapGap);

      // 3-Way Synchronization
      function syncOtherMaps(sourceMap, targetMaps) {
        sourceMap.on('move', () => {
          if (!isSyncing) {
            isSyncing = true;
            const c = sourceMap.getCenter();
            const z = sourceMap.getZoom();
            targetMaps.forEach(m => {
              if (m) m.setView(c, z, { animate: false });
            });
            isSyncing = false;
          }
        });
      }

      syncOtherMaps(mapRisk, [mapBudget, mapGap]);
      syncOtherMaps(mapBudget, [mapRisk, mapGap]);
      syncOtherMaps(mapGap, [mapRisk, mapBudget]);

      window.addEventListener('resize', () => {
        if (mapRisk) mapRisk.invalidateSize();
        if (mapBudget) mapBudget.invalidateSize();
        if (mapGap) mapGap.invalidateSize();
      });
    }

    /* ========================================================= */
    /* LAYOUT SWITCHER                                           */
    /* ========================================================= */
    function setLayoutMode(mode) {
      currentLayout = mode;
      const wrapper = document.getElementById('mapWrapper');
      const boxRisk = document.getElementById('boxRisk');
      const boxBudget = document.getElementById('boxBudget');
      const boxGap = document.getElementById('boxGap');

      document.querySelectorAll('.layout-btn').forEach(b => b.classList.remove('active'));

      if (mode === 'triple') {
        document.getElementById('btnLayoutTriple').classList.add('active');
        wrapper.style.gridTemplateColumns = '1fr 1fr 1fr';
        boxRisk.style.display = 'block';
        boxBudget.style.display = 'block';
        boxGap.style.display = 'block';
      } else if (mode === 'risk-gap') {
        document.getElementById('btnLayoutRiskGap').classList.add('active');
        wrapper.style.gridTemplateColumns = '1fr 1fr';
        boxRisk.style.display = 'block';
        boxBudget.style.display = 'none';
        boxGap.style.display = 'block';
      } else if (mode === 'budget-gap') {
        document.getElementById('btnLayoutBudgetGap').classList.add('active');
        wrapper.style.gridTemplateColumns = '1fr 1fr';
        boxRisk.style.display = 'none';
        boxBudget.style.display = 'block';
        boxGap.style.display = 'block';
      } else if (mode === 'gap-only') {
        document.getElementById('btnLayoutGapOnly').classList.add('active');
        wrapper.style.gridTemplateColumns = '1fr';
        boxRisk.style.display = 'none';
        boxBudget.style.display = 'none';
        boxGap.style.display = 'block';
      }

      setTimeout(() => {
        if (mapRisk) mapRisk.invalidateSize();
        if (mapBudget) mapBudget.invalidateSize();
        if (mapGap) mapGap.invalidateSize();
      }, 350);
    }

    /* ========================================================= */
    /* COLOR SCHEMES & GAP STYLING                               */
    /* ========================================================= */
    function getDistrictRiskColor(highRiskCount) {
      if (highRiskCount >= 100) return '#b71c1c';
      if (highRiskCount >= 50) return '#e53935';
      if (highRiskCount >= 20) return '#fb8c00';
      if (highRiskCount >= 5) return '#fdd835';
      return '#43a047';
    }

    function getDistrictBudgetColor(budget) {
      if (budget >= 3000) return '#0d47a1';
      if (budget >= 1500) return '#1976d2';
      if (budget >= 800) return '#42a5f5';
      if (budget >= 400) return '#90caf9';
      return '#e3f2fd';
    }

    function getGapColor(gapStatus) {
      if (!gapStatus) return '#22c55e';
      if (gapStatus.includes('วิกฤติ') || gapStatus.includes('ไม่เพียงพอ')) return '#ef4444'; // Red
      if (gapStatus.includes('เสี่ยงสูง - ได้รับงบประมาณ')) return '#f97316'; // Orange
      if (gapStatus.includes('เสี่ยงปานกลาง')) return '#eab308'; // Yellow
      if (gapStatus.includes('งบประมาณสูง - ความเสี่ยงต่ำ')) return '#3b82f6'; // Blue
      return '#22c55e'; // Green
    }

    function getGapBadgeClass(gapStatus) {
      if (!gapStatus) return 'pill-gap-green';
      if (gapStatus.includes('วิกฤติ')) return 'pill-gap-red';
      if (gapStatus.includes('เสี่ยงสูง')) return 'pill-gap-orange';
      if (gapStatus.includes('เสี่ยงปานกลาง')) return 'pill-gap-yellow';
      if (gapStatus.includes('งบประมาณสูง')) return 'pill-gap-blue';
      return 'pill-gap-green';
    }

    function getVillageColor(totalScore) {
      if (totalScore >= 12) return '#ef4444'; // Red
      if (totalScore >= 10) return '#f97316'; // Orange
      if (totalScore >= 8) return '#eab308';  // Yellow
      return '#22c55e'; // Green
    }

    /* ========================================================= */
    /* RENDER ALL GIS LAYERS WITH CLEAR DISTRICT BOUNDARIES     */
    /* ========================================================= */
    function renderAllLayers() {
      // 1. DISTRICTS LAYER WITH DISTINCT BOUNDARY OUTLINES
      const distRiskLayer = L.geoJSON(DISTRICTS_DATA, {
        style: (feature) => ({
          fillColor: getDistrictRiskColor(feature.properties.high_risk_total || 0),
          fillOpacity: 0.65,
          color: '#1e293b', // Crisp Solid Dark Boundary Outline
          weight: 2.2,
          opacity: 0.95
        }),
        onEachFeature: (feature, layer) => {
          const name = feature.properties.amp_th;
          districtLayersRisk[name] = layer;
          
          // District Name Badge
          layer.bindTooltip(
            `<div class="district-label-card"><b>อ.${name}</b><div class="district-sublabel">เสี่ยงสูง ${feature.properties.high_risk_total || 0} จุด</div></div>`,
            { permanent: false, direction: 'center', opacity: 0.95 }
          );

          layer.on('mouseover', (e) => {
            e.target.setStyle({ weight: 3.5, color: '#000000', fillOpacity: 0.85 });
          });
          layer.on('mouseout', (e) => {
            distRiskLayer.resetStyle(e.target);
          });
          layer.on('click', () => selectDistrict(name));
        }
      }).addTo(mapRisk);

      const distBudgetLayer = L.geoJSON(DISTRICTS_DATA, {
        style: (feature) => ({
          fillColor: getDistrictBudgetColor(feature.properties.total_budget || 0),
          fillOpacity: 0.7,
          color: '#1e293b', // Crisp Solid Dark Boundary Outline
          weight: 2.2,
          opacity: 0.95
        }),
        onEachFeature: (feature, layer) => {
          const name = feature.properties.amp_th;
          districtLayersBudget[name] = layer;
          const bgText = Number(feature.properties.total_budget || 0).toLocaleString('th-TH', {maximumFractionDigits:1});
          
          layer.bindTooltip(
            `<div class="district-label-card"><b>อ.${name}</b><div class="district-sublabel">${bgText} ลบ. (${feature.properties.total_projects || 0} โครงการ)</div></div>`,
            { permanent: false, direction: 'center', opacity: 0.95 }
          );

          layer.on('mouseover', (e) => {
            e.target.setStyle({ weight: 3.5, color: '#000000', fillOpacity: 0.85 });
          });
          layer.on('mouseout', (e) => {
            distBudgetLayer.resetStyle(e.target);
          });
          layer.on('click', () => selectDistrict(name));
        }
      }).addTo(mapBudget);

      const distGapLayer = L.geoJSON(DISTRICTS_DATA, {
        style: (feature) => ({
          fillColor: getGapColor(feature.properties.gap_status),
          fillOpacity: 0.75,
          color: '#1e293b', // Crisp Solid Dark Boundary Outline
          weight: 2.2,
          opacity: 0.95
        }),
        onEachFeature: (feature, layer) => {
          const name = feature.properties.amp_th;
          districtLayersGap[name] = layer;
          const status = feature.properties.gap_status || '🟢 สมดุล';
          
          layer.bindTooltip(
            `<div class="district-label-card"><b>อ.${name}</b><div class="district-sublabel">${status.split(' - ')[0]}</div></div>`,
            { permanent: false, direction: 'center', opacity: 0.95 }
          );

          layer.on('mouseover', (e) => {
            e.target.setStyle({ weight: 3.5, color: '#000000', fillOpacity: 0.85 });
          });
          layer.on('mouseout', (e) => {
            distGapLayer.resetStyle(e.target);
          });
          layer.on('click', () => selectDistrict(name));
        }
      }).addTo(mapGap);

      cmBounds = distRiskLayer.getBounds();

      // 2. SUBDISTRICTS LAYER GROUP (Clean dashed boundary when zooming)
      subdistrictGroupRisk = L.geoJSON(SUBDISTRICTS_DATA, {
        style: (feature) => ({
          fillColor: getDistrictRiskColor(feature.properties.high_risk_total || 0),
          fillOpacity: 0.55,
          color: '#334155',
          weight: 1.5,
          dashArray: '3, 3'
        }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindTooltip(`<b>ต.${p.tam_th}</b> (อ.${p.amp_th})<br>เสี่ยงสูง ${p.high_risk_total || 0} จุด`, { direction: 'center' });
          layer.on('click', () => selectSubdistrict(p.amp_th, p.tam_th));
        }
      });

      subdistrictGroupBudget = L.geoJSON(SUBDISTRICTS_DATA, {
        style: (feature) => ({
          fillColor: getDistrictBudgetColor(feature.properties.total_budget || 0),
          fillOpacity: 0.6,
          color: '#334155',
          weight: 1.5,
          dashArray: '3, 3'
        }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          const bgText = Number(p.total_budget || 0).toLocaleString('th-TH', {maximumFractionDigits:1});
          layer.bindTooltip(`<b>ต.${p.tam_th}</b><br>${bgText} ลบ.`, { direction: 'center' });
          layer.on('click', () => selectSubdistrict(p.amp_th, p.tam_th));
        }
      });

      subdistrictGroupGap = L.geoJSON(SUBDISTRICTS_DATA, {
        style: (feature) => ({
          fillColor: getGapColor(feature.properties.gap_status),
          fillOpacity: 0.7,
          color: '#334155',
          weight: 1.5,
          dashArray: '3, 3'
        }),
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          const status = p.gap_status || '🟢 สมดุล';
          layer.bindTooltip(`<b>ต.${p.tam_th}</b><br>${status.split(' - ')[0]}`, { direction: 'center' });
          layer.on('click', () => selectSubdistrict(p.amp_th, p.tam_th));
        }
      });

      // 3. VILLAGES PINS LAYER (Controlled by showVillages flag)
      renderVillagePins();
    }

    function toggleVillagePins() {
      showVillages = !showVillages;
      const btn = document.getElementById('btnTogglePins');
      const txt = document.getElementById('txtTogglePins');
      
      if (showVillages) {
        btn.classList.add('active');
        txt.textContent = 'ซ่อนหมุดหมู่บ้าน (เปิดอยู่)';
      } else {
        btn.classList.remove('active');
        txt.textContent = 'แสดงหมุดหมู่บ้าน (ปิดอยู่)';
      }
      renderVillagePins();
    }

    function renderVillagePins() {
      if (villagePointsRisk) mapRisk.removeLayer(villagePointsRisk);
      if (villagePointsBudget) mapBudget.removeLayer(villagePointsBudget);
      if (villagePointsGap) mapGap.removeLayer(villagePointsGap);

      // If user turned off pins and not in village level, do not render to keep overview clean
      if (!showVillages && selectedVillageId === 'all' && selectedDistrict === 'all') {
        return;
      }

      villagePointsRisk = L.layerGroup();
      villagePointsBudget = L.layerGroup();
      villagePointsGap = L.layerGroup();

      VILLAGES_DATA.features.forEach(feat => {
        const p = feat.properties;
        const [lng, lat] = feat.geometry.coordinates;

        // Apply Filters
        if (selectedDistrict !== 'all' && p.district !== selectedDistrict) return;
        if (selectedSubdistrict !== 'all' && p.subdistrict !== selectedSubdistrict) return;
        if (selectedPillar !== 'all') {
          const pScore = p[`p${selectedPillar}_score`];
          if (pScore === 1) return;
        }

        const color = getVillageColor(p.total_score || 0);

        // Marker for Risk Map
        const markerRisk = L.circleMarker([lat, lng], {
          radius: 5,
          fillColor: color,
          color: '#ffffff',
          weight: 1,
          opacity: 1,
          fillOpacity: 0.85
        }).bindTooltip(`<b>ม.${p.village}</b> (ต.${p.subdistrict})<br>คะแนนรวม: ${p.total_score}/15 (${p.priority})`);
        markerRisk.on('click', () => selectVillage(p.id));
        villagePointsRisk.addLayer(markerRisk);

        // Marker for Budget Map
        const markerBudget = L.circleMarker([lat, lng], {
          radius: 5,
          fillColor: '#1a73e8',
          color: '#ffffff',
          weight: 1,
          opacity: 1,
          fillOpacity: 0.8
        }).bindTooltip(`<b>ม.${p.village}</b><br>ต.${p.subdistrict} อ.${p.district}`);
        markerBudget.on('click', () => selectVillage(p.id));
        villagePointsBudget.addLayer(markerBudget);

        // Marker for Gap Map
        const markerGap = L.circleMarker([lat, lng], {
          radius: 5,
          fillColor: color,
          color: '#7c3aed',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85
        }).bindTooltip(`<b>ม.${p.village}</b><br>ความเสี่ยง: ${p.total_score}/15<br>ต.${p.subdistrict}`);
        markerGap.on('click', () => selectVillage(p.id));
        villagePointsGap.addLayer(markerGap);
      });

      villagePointsRisk.addTo(mapRisk);
      villagePointsBudget.addTo(mapBudget);
      villagePointsGap.addTo(mapGap);
    }

    /* ========================================================= */
    /* 3-TIER DROPDOWNS & FILTER LOGIC                           */
    /* ========================================================= */
    function populateDropdowns() {
      const distSelect = document.getElementById('districtSelect');
      const districts = [...new Set(DISTRICTS_DATA.features.map(f => f.properties.amp_th))].sort((a,b) => a.localeCompare(b, 'th'));
      
      distSelect.innerHTML = '<option value="all">📍 ทุกอำเภอ (25 อำเภอ)</option>';
      districts.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d;
        opt.textContent = `อ.${d}`;
        distSelect.appendChild(opt);
      });

      updateSubdistrictDropdown('all');
      updateVillageDropdown('all', 'all');
    }

    function updateSubdistrictDropdown(district) {
      const subSelect = document.getElementById('subdistrictSelect');
      subSelect.innerHTML = '<option value="all">🏘️ ทุกตำบล (204 ตำบล)</option>';

      let subdistricts = SUBDISTRICTS_DATA.features;
      if (district !== 'all') {
        subdistricts = subdistricts.filter(f => f.properties.amp_th === district);
      }
      const subs = [...new Set(subdistricts.map(f => f.properties.tam_th))].sort((a,b) => a.localeCompare(b, 'th'));
      subs.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = `ต.${s}`;
        subSelect.appendChild(opt);
      });
    }

    function updateVillageDropdown(district, subdistrict) {
      const vSelect = document.getElementById('villageSelect');
      vSelect.innerHTML = '<option value="all">🏡 ทุกหมู่บ้าน (2,200 หมู่บ้าน)</option>';

      let villages = VILLAGES_DATA.features;
      if (district !== 'all') villages = villages.filter(f => f.properties.district === district);
      if (subdistrict !== 'all') villages = villages.filter(f => f.properties.subdistrict === subdistrict);

      villages.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.properties.id;
        opt.textContent = `ม.${v.properties.village} (ต.${v.properties.subdistrict})`;
        vSelect.appendChild(opt);
      });
    }

    /* ========================================================= */
    /* SELECTION & DRILLDOWN FUNCTIONS                           */
    /* ========================================================= */
    function selectDistrict(name) {
      selectedDistrict = name;
      selectedSubdistrict = 'all';
      selectedVillageId = 'all';

      document.getElementById('districtSelect').value = name;
      updateSubdistrictDropdown(name);
      updateVillageDropdown(name, 'all');

      // Zoom to district bounds
      const layer = districtLayersRisk[name];
      if (layer) {
        const b = layer.getBounds();
        isSyncing = true;
        mapRisk.fitBounds(b, { padding: [30, 30] });
        mapBudget.fitBounds(b, { padding: [30, 30] });
        mapGap.fitBounds(b, { padding: [30, 30] });
        isSyncing = false;
      }

      // Show subdistricts on zoom
      if (!mapRisk.hasLayer(subdistrictGroupRisk)) {
        mapRisk.addLayer(subdistrictGroupRisk);
        mapBudget.addLayer(subdistrictGroupBudget);
        mapGap.addLayer(subdistrictGroupGap);
      }

      renderVillagePins();
      updateDockForDistrict(name);
      showFloatingBack('ย้อนกลับภาพรวม จ.เชียงใหม่');
    }

    function selectSubdistrict(district, subdistrict) {
      selectedDistrict = district;
      selectedSubdistrict = subdistrict;
      selectedVillageId = 'all';

      document.getElementById('districtSelect').value = district;
      updateSubdistrictDropdown(district);
      document.getElementById('subdistrictSelect').value = subdistrict;
      updateVillageDropdown(district, subdistrict);

      // Find subdistrict feature and zoom
      const feat = SUBDISTRICTS_DATA.features.find(f => f.properties.amp_th === district && f.properties.tam_th === subdistrict);
      if (feat) {
        const layer = L.geoJSON(feat);
        const b = layer.getBounds();
        isSyncing = true;
        mapRisk.fitBounds(b, { padding: [35, 35] });
        mapBudget.fitBounds(b, { padding: [35, 35] });
        mapGap.fitBounds(b, { padding: [35, 35] });
        isSyncing = false;
      }

      renderVillagePins();
      updateDockForSubdistrict(district, subdistrict);
      showFloatingBack(`ย้อนกลับ อ.${district}`);
    }

    function selectVillage(id) {
      selectedVillageId = id;
      const feat = VILLAGES_DATA.features.find(f => f.properties.id === parseInt(id));
      if (!feat) return;

      const p = feat.properties;
      selectedDistrict = p.district;
      selectedSubdistrict = p.subdistrict;

      document.getElementById('districtSelect').value = p.district;
      updateSubdistrictDropdown(p.district);
      document.getElementById('subdistrictSelect').value = p.subdistrict;
      updateVillageDropdown(p.district, p.subdistrict);
      document.getElementById('villageSelect').value = p.id;

      const [lng, lat] = feat.geometry.coordinates;
      isSyncing = true;
      mapRisk.setView([lat, lng], 15);
      mapBudget.setView([lat, lng], 15);
      mapGap.setView([lat, lng], 15);
      isSyncing = false;

      // Pulse Beacons on all 3 maps
      if (activePulseRisk) mapRisk.removeLayer(activePulseRisk);
      if (activePulseBudget) mapBudget.removeLayer(activePulseBudget);
      if (activePulseGap) mapGap.removeLayer(activePulseGap);

      const pulseIcon = L.divIcon({ className: 'pulsing-beacon', iconSize: [22, 22], iconAnchor: [11, 11] });
      const pulseIconGap = L.divIcon({ className: 'pulsing-beacon pulsing-beacon-gap', iconSize: [22, 22], iconAnchor: [11, 11] });

      activePulseRisk = L.marker([lat, lng], { icon: pulseIcon }).addTo(mapRisk);
      activePulseBudget = L.marker([lat, lng], { icon: pulseIcon }).addTo(mapBudget);
      activePulseGap = L.marker([lat, lng], { icon: pulseIconGap }).addTo(mapGap);

      updateDockForVillage(p);
      showFloatingBack(`ย้อนกลับ ต.${p.subdistrict}`);
    }

    /* ========================================================= */
    /* BOTTOM DOCK & GAP MATRIX UPDATE                           */
    /* ========================================================= */
    function updateDockForOverview() {
      document.getElementById('dockBreadcrumbs').innerHTML = `<span class="bc-active">📍 จ.เชียงใหม่ (ภาพรวม 25 อำเภอ)</span>`;
      document.getElementById('dockPillGap').className = 'dock-stat-pill pill-gap-red';
      document.getElementById('dockPillGap').textContent = '🚨 Gap วิกฤติ 3 อำเภอ (สารภี/สันกำแพง/แม่อาย)';
      document.getElementById('dockPillRisk').textContent = '🔴 เสี่ยงสูง 1,040 จุด';
      document.getElementById('dockPillBudget').textContent = '💰 35,094.77 ลบ. (6,312 โครงการ)';

      // Expanded Content: 5 Pillars Gap Matrix
      let bodyHtml = `
        <div style="margin-bottom:10px; font-weight:700; color:#202124; font-size:0.82rem; display:flex; justify-content:space-between;">
          <span>📊 สรุปความสอดคล้อง 5 มิติ แผนแม่บทน้ำ จ.เชียงใหม่ (2565-2570)</span>
          <span style="color:#7c3aed; font-weight:600;">⚡ Gap Ratio รวม: 33.74 ลบ./จุดเสี่ยงสูง</span>
        </div>
        <table class="gap-table">
          <thead>
            <tr>
              <th>มิติแผนแม่บท (5 ด้าน)</th>
              <th style="text-align:center;">จุดเสี่ยงสูง</th>
              <th style="text-align:center;">จุดเฝ้าระวัง</th>
              <th style="text-align:right;">จำนวนโครงการ</th>
              <th style="text-align:right;">งบประมาณรวม</th>
              <th style="text-align:center;">สถานะ Gap ความสอดคล้อง</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>💧 ด้าน 1: น้ำอุปโภคบริโภค</b></td>
              <td style="text-align:center; color:#c5221f; font-weight:700;">39</td>
              <td style="text-align:center;">522</td>
              <td style="text-align:right;">721</td>
              <td style="text-align:right; font-weight:700; color:#1a73e8;">2,266.62 ลบ.</td>
              <td style="text-align:center;"><span class="dock-stat-pill pill-gap-green">🟢 สมดุลตามเกณฑ์</span></td>
            </tr>
            <tr>
              <td><b>🌾 ด้าน 2: น้ำภาคการผลิต (เกษตร)</b></td>
              <td style="text-align:center; color:#c5221f; font-weight:700;">142</td>
              <td style="text-align:center;">1,231</td>
              <td style="text-align:right;">2,349</td>
              <td style="text-align:right; font-weight:700; color:#1a73e8;">23,454.85 ลบ.</td>
              <td style="text-align:center;"><span class="dock-stat-pill pill-gap-blue">🔵 งบสูง (โครงการชลประทานหลัก)</span></td>
            </tr>
            <tr>
              <td><b>🌊 ด้าน 3: น้ำท่วมและอุทกภัย</b></td>
              <td style="text-align:center; color:#c5221f; font-weight:700;">180</td>
              <td style="text-align:center;">1,116</td>
              <td style="text-align:right;">356</td>
              <td style="text-align:right; font-weight:700; color:#1a73e8;">4,391.91 ลบ.</td>
              <td style="text-align:center;"><span class="dock-stat-pill pill-gap-orange">⚠️ เสี่ยงสูง - งบกระจุกตัวตัวเมือง</span></td>
            </tr>
            <tr>
              <td><b>🧪 ด้าน 4: คุณภาพน้ำและอนุรักษ์</b></td>
              <td style="text-align:center; color:#c5221f; font-weight:700;">188</td>
              <td style="text-align:center;">846</td>
              <td style="text-align:right;">2,774</td>
              <td style="text-align:right; font-weight:700; color:#1a73e8;">4,131.87 ลบ.</td>
              <td style="text-align:center;"><span class="dock-stat-pill pill-gap-green">🟢 สมดุลโครงการกระจายตัว</span></td>
            </tr>
            <tr>
              <td><b>🌲 ด้าน 5: ฟื้นฟูป่าต้นน้ำและชะล้างดิน</b></td>
              <td style="text-align:center; color:#c5221f; font-weight:700;">491</td>
              <td style="text-align:center;">478</td>
              <td style="text-align:right;">112</td>
              <td style="text-align:right; font-weight:700; color:#1a73e8;">849.52 ลบ.</td>
              <td style="text-align:center;"><span class="dock-stat-pill pill-gap-red">🚨 เสี่ยงสูงวิกฤติ - งบต่ำสุด (1.73 ลบ./จุด)</span></td>
            </tr>
          </tbody>
        </table>
      `;
      document.getElementById('dockExpandedBody').innerHTML = bodyHtml;
    }

    function updateDockForDistrict(distName) {
      const feat = DISTRICTS_DATA.features.find(f => f.properties.amp_th === distName);
      if (!feat) return;
      const p = feat.properties;

      document.getElementById('dockBreadcrumbs').innerHTML = `
        <span class="bc-item" onclick="resetToOverview()">📍 จ.เชียงใหม่</span>
        <span class="bc-separator">❯</span>
        <span class="bc-active">🏛️ อ.${p.amp_th}</span>
      `;

      const gapClass = getGapBadgeClass(p.gap_status);
      document.getElementById('dockPillGap').className = `dock-stat-pill ${gapClass}`;
      document.getElementById('dockPillGap').textContent = p.gap_status || '🟢 สมดุล';
      document.getElementById('dockPillRisk').textContent = `🔴 เสี่ยงสูง ${p.high_risk_total || 0} จุด (${p.villages || 0} หมู่บ้าน)`;
      const totalBudgetFormatted = Number(p.total_budget || 0).toLocaleString('th-TH', {maximumFractionDigits:1});
      document.getElementById('dockPillBudget').textContent = `💰 ${totalBudgetFormatted} ลบ. (${p.total_projects || 0} โครงการ)`;

      let bodyHtml = `
        <div style="margin-bottom:8px; font-weight:700; color:#202124; font-size:0.8rem; display:flex; justify-content:space-between;">
          <span>🏛️ รายละเอียดความสอดคล้องรายมิติ อ.${p.amp_th} (งบเฉลี่ย ${Number(p.avg_budget_per_high || 0).toFixed(2)} ลบ./จุดเสี่ยงสูง)</span>
          <span class="dock-stat-pill ${gapClass}">${p.gap_status || '🟢 สมดุล'}</span>
        </div>
        <table class="gap-table">
          <thead>
            <tr>
              <th>มิติแผนแม่บทน้ำ</th>
              <th style="text-align:center;">จุดเสี่ยงสูง</th>
              <th style="text-align:right;">โครงการ</th>
              <th style="text-align:right;">งบประมาณจัดสรร</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>💧 ด้าน 1: น้ำอุปโภคบริโภค</td>
              <td style="text-align:center; font-weight:700; color:${p.high_p1 > 0 ? '#c5221f' : '#202124'}">${p.high_p1 || 0}</td>
              <td style="text-align:right;">${p.proj_p1 || 0}</td>
              <td style="text-align:right; font-weight:600;">${Number(p.budget_p1 || 0).toFixed(2)} ลบ.</td>
            </tr>
            <tr>
              <td>🌾 ด้าน 2: น้ำภาคเกษตร</td>
              <td style="text-align:center; font-weight:700; color:${p.high_p2 > 0 ? '#c5221f' : '#202124'}">${p.high_p2 || 0}</td>
              <td style="text-align:right;">${p.proj_p2 || 0}</td>
              <td style="text-align:right; font-weight:600;">${Number(p.budget_p2 || 0).toFixed(2)} ลบ.</td>
            </tr>
            <tr>
              <td>🌊 ด้าน 3: น้ำท่วมและอุทกภัย</td>
              <td style="text-align:center; font-weight:700; color:${p.high_p3 > 0 ? '#c5221f' : '#202124'}">${p.high_p3 || 0}</td>
              <td style="text-align:right;">${p.proj_p3 || 0}</td>
              <td style="text-align:right; font-weight:600;">${Number(p.budget_p3 || 0).toFixed(2)} ลบ.</td>
            </tr>
            <tr>
              <td>🧪 ด้าน 4: คุณภาพน้ำและการอนุรักษ์</td>
              <td style="text-align:center; font-weight:700; color:${p.high_p4 > 0 ? '#c5221f' : '#202124'}">${p.high_p4 || 0}</td>
              <td style="text-align:right;">${p.proj_p4 || 0}</td>
              <td style="text-align:right; font-weight:600;">${Number(p.budget_p4 || 0).toFixed(2)} ลบ.</td>
            </tr>
            <tr>
              <td>🌲 ด้าน 5: ฟื้นฟูป่าต้นน้ำและชะล้างดิน</td>
              <td style="text-align:center; font-weight:700; color:${p.high_p5 > 0 ? '#c5221f' : '#202124'}">${p.high_p5 || 0}</td>
              <td style="text-align:right;">${p.proj_p5 || 0}</td>
              <td style="text-align:right; font-weight:600;">${Number(p.budget_p5 || 0).toFixed(2)} ลบ.</td>
            </tr>
          </tbody>
        </table>
      `;
      document.getElementById('dockExpandedBody').innerHTML = bodyHtml;
    }

    function updateDockForSubdistrict(distName, subName) {
      const feat = SUBDISTRICTS_DATA.features.find(f => f.properties.amp_th === distName && f.properties.tam_th === subName);
      if (!feat) return;
      const p = feat.properties;

      document.getElementById('dockBreadcrumbs').innerHTML = `
        <span class="bc-item" onclick="resetToOverview()">📍 จ.เชียงใหม่</span>
        <span class="bc-separator">❯</span>
        <span class="bc-item" onclick="selectDistrict('${distName}')">🏛️ อ.${distName}</span>
        <span class="bc-separator">❯</span>
        <span class="bc-active">🏘️ ต.${subName}</span>
      `;

      const gapClass = getGapBadgeClass(p.gap_status);
      document.getElementById('dockPillGap').className = `dock-stat-pill ${gapClass}`;
      document.getElementById('dockPillGap').textContent = p.gap_status || '🟢 สมดุล';
      document.getElementById('dockPillRisk').textContent = `🔴 เสี่ยงสูง ${p.high_risk_total || 0} จุด (${p.villages || 0} หมู่บ้าน)`;
      const subBudgetFormatted = Number(p.total_budget || 0).toFixed(2);
      document.getElementById('dockPillBudget').textContent = `💰 ${subBudgetFormatted} ลบ. (${p.total_projects || 0} โครงการ)`;

      let bodyHtml = `
        <div style="margin-bottom:8px; font-weight:700; color:#202124; font-size:0.8rem; display:flex; justify-content:space-between;">
          <span>🏘️ สรุปรายมิติ ต.${subName} (อ.${distName})</span>
          <span class="dock-stat-pill ${gapClass}">${p.gap_status || '🟢 สมดุล'}</span>
        </div>
        <table class="gap-table">
          <thead>
            <tr>
              <th>มิติแผนแม่บทน้ำ</th>
              <th style="text-align:center;">จุดเสี่ยงสูง</th>
              <th style="text-align:right;">งบประมาณจัดสรร (ลบ.)</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>💧 ด้าน 1: น้ำอุปโภคบริโภค</td><td style="text-align:center; font-weight:700;">${p.high_p1 || 0}</td><td style="text-align:right;">${Number(p.budget_p1 || 0).toFixed(2)}</td></tr>
            <tr><td>🌾 ด้าน 2: น้ำภาคเกษตร</td><td style="text-align:center; font-weight:700;">${p.high_p2 || 0}</td><td style="text-align:right;">${Number(p.budget_p2 || 0).toFixed(2)}</td></tr>
            <tr><td>🌊 ด้าน 3: น้ำท่วมและอุทกภัย</td><td style="text-align:center; font-weight:700;">${p.high_p3 || 0}</td><td style="text-align:right;">${Number(p.budget_p3 || 0).toFixed(2)}</td></tr>
            <tr><td>🧪 ด้าน 4: คุณภาพน้ำและการอนุรักษ์</td><td style="text-align:center; font-weight:700;">${p.high_p4 || 0}</td><td style="text-align:right;">${Number(p.budget_p4 || 0).toFixed(2)}</td></tr>
            <tr><td>🌲 ด้าน 5: ฟื้นฟูป่าต้นน้ำและชะล้างดิน</td><td style="text-align:center; font-weight:700;">${p.high_p5 || 0}</td><td style="text-align:right;">${Number(p.budget_p5 || 0).toFixed(2)}</td></tr>
          </tbody>
        </table>
      `;
      document.getElementById('dockExpandedBody').innerHTML = bodyHtml;
    }

    function updateDockForVillage(p) {
      document.getElementById('dockBreadcrumbs').innerHTML = `
        <span class="bc-item" onclick="resetToOverview()">📍 จ.เชียงใหม่</span>
        <span class="bc-separator">❯</span>
        <span class="bc-item" onclick="selectDistrict('${p.district}')">🏛️ อ.${p.district}</span>
        <span class="bc-separator">❯</span>
        <span class="bc-item" onclick="selectSubdistrict('${p.district}', '${p.subdistrict}')">🏘️ ต.${p.subdistrict}</span>
        <span class="bc-separator">❯</span>
        <span class="bc-active">🏡 ม.${p.village}</span>
      `;

      document.getElementById('dockPillGap').className = 'dock-stat-pill pill-score';
      document.getElementById('dockPillGap').textContent = `⭐ คะแนนรวม ${p.total_score}/15`;
      document.getElementById('dockPillRisk').textContent = `${p.priority}`;
      document.getElementById('dockPillBudget').textContent = `🔴 เสี่ยงสูง ${p.high_count} | 🟡 กลาง ${p.med_count} | 🟢 น้อย ${p.low_count}`;

      let bodyHtml = `
        <div style="margin-bottom:8px; font-weight:700; color:#202124; font-size:0.8rem;">
          🏡 ผลประเมินความมั่นคงด้านน้ำ 5 มิติ: ม.${p.village} ต.${p.subdistrict} อ.${p.district}
        </div>
        <table class="gap-table">
          <thead>
            <tr>
              <th>มิติแผนแม่บทน้ำ</th>
              <th style="text-align:center;">คะแนน (เต็ม 3)</th>
              <th style="text-align:left;">ระดับความเสี่ยง</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>💧 ด้าน 1: น้ำอุปโภคบริโภค</td><td style="text-align:center; font-weight:700;">${p.p1_score}</td><td>${p.p1_text}</td></tr>
            <tr><td>🌾 ด้าน 2: น้ำภาคเกษตร</td><td style="text-align:center; font-weight:700;">${p.p2_score}</td><td>${p.p2_text}</td></tr>
            <tr><td>🌊 ด้าน 3: น้ำท่วมและอุทกภัย</td><td style="text-align:center; font-weight:700;">${p.p3_score}</td><td>${p.p3_text}</td></tr>
            <tr><td>🧪 ด้าน 4: คุณภาพน้ำและการอนุรักษ์</td><td style="text-align:center; font-weight:700;">${p.p4_score}</td><td>${p.p4_text}</td></tr>
            <tr><td>🌲 ด้าน 5: ฟื้นฟูป่าต้นน้ำและชะล้างดิน</td><td style="text-align:center; font-weight:700;">${p.p5_score}</td><td>${p.p5_text}</td></tr>
          </tbody>
        </table>
      `;
      document.getElementById('dockExpandedBody').innerHTML = bodyHtml;
    }

    function toggleDockExpand() {
      const dock = document.getElementById('smartDock');
      dock.classList.toggle('expanded');
      const isExp = dock.classList.contains('expanded');
      document.getElementById('expandIcon').textContent = isExp ? 'expand_more' : 'expand_less';
      document.getElementById('expandText').textContent = isExp ? 'ย่อตาราง' : 'ดูตาราง Gap 5 มิติ';
    }

    function closeDock() {
      document.getElementById('smartDock').style.display = 'none';
    }

    /* ========================================================= */
    /* FLOATING BACK BUTTON & RESET                              */
    /* ========================================================= */
    function showFloatingBack(text) {
      const bar = document.getElementById('floatingBackBar');
      document.getElementById('floatingBackText').textContent = text;
      bar.style.display = 'block';
    }

    function resetToOverview() {
      selectedDistrict = 'all';
      selectedSubdistrict = 'all';
      selectedVillageId = 'all';
      selectedGapFilter = 'all';
      selectedPillar = 'all';

      document.getElementById('districtSelect').value = 'all';
      document.getElementById('subdistrictSelect').value = 'all';
      document.getElementById('villageSelect').value = 'all';
      document.getElementById('gapStatusSelect').value = 'all';
      document.getElementById('pillarSelect').value = 'all';
      document.getElementById('searchInput').value = '';

      if (activePulseRisk) mapRisk.removeLayer(activePulseRisk);
      if (activePulseBudget) mapBudget.removeLayer(activePulseBudget);
      if (activePulseGap) mapGap.removeLayer(activePulseGap);

      if (subdistrictGroupRisk && mapRisk.hasLayer(subdistrictGroupRisk)) {
        mapRisk.removeLayer(subdistrictGroupRisk);
        mapBudget.removeLayer(subdistrictGroupBudget);
        mapGap.removeLayer(subdistrictGroupGap);
      }

      isSyncing = true;
      if (cmBounds) {
        mapRisk.fitBounds(cmBounds, { padding: [20, 20] });
        mapBudget.fitBounds(cmBounds, { padding: [20, 20] });
        mapGap.fitBounds(cmBounds, { padding: [20, 20] });
      }
      isSyncing = false;

      document.getElementById('floatingBackBar').style.display = 'none';
      document.getElementById('smartDock').style.display = 'block';
      updateDockForOverview();
      renderVillagePins();
    }

    /* ========================================================= */
    /* EVENT HANDLERS                                            */
    /* ========================================================= */
    function handleDistrictSelect(val) {
      if (val === 'all') resetToOverview();
      else selectDistrict(val);
    }

    function handleSubdistrictSelect(val) {
      if (val === 'all') {
        if (selectedDistrict !== 'all') selectDistrict(selectedDistrict);
        else resetToOverview();
      } else {
        let d = selectedDistrict;
        if (d === 'all') {
          const feat = SUBDISTRICTS_DATA.features.find(f => f.properties.tam_th === val);
          if (feat) d = feat.properties.amp_th;
        }
        selectSubdistrict(d, val);
      }
    }

    function handleVillageSelect(val) {
      if (val === 'all') {
        if (selectedSubdistrict !== 'all') selectSubdistrict(selectedDistrict, selectedSubdistrict);
        else if (selectedDistrict !== 'all') selectDistrict(selectedDistrict);
        else resetToOverview();
      } else {
        selectVillage(val);
      }
    }

    function handleGapFilter(val) {
      selectedGapFilter = val;
      // Filter districts and subdistricts on mapGap
      Object.keys(districtLayersGap).forEach(dName => {
        const layer = districtLayersGap[dName];
        const status = layer.feature.properties.gap_status || '';
        if (val === 'all' || status.includes(val) || val.includes(status.split(' - ')[0])) {
          layer.setStyle({ fillOpacity: 0.75, opacity: 1, color: '#1e293b', weight: 2.2 });
        } else {
          layer.setStyle({ fillOpacity: 0.08, opacity: 0.2, color: '#94a3b8', weight: 1 });
        }
      });
    }

    function handlePillarSelect(val) {
      selectedPillar = val;
      renderVillagePins();
    }

    function handleSearch(query) {
      const q = query.trim().toLowerCase();
      if (!q) {
        renderVillagePins();
        return;
      }
      // Check district match
      const matchedDist = DISTRICTS_DATA.features.find(f => f.properties.amp_th.toLowerCase().includes(q));
      if (matchedDist) {
        selectDistrict(matchedDist.properties.amp_th);
        return;
      }
      // Check subdistrict match
      const matchedSub = SUBDISTRICTS_DATA.features.find(f => f.properties.tam_th.toLowerCase().includes(q));
      if (matchedSub) {
        selectSubdistrict(matchedSub.properties.amp_th, matchedSub.properties.tam_th);
        return;
      }
      // Check village match
      const matchedV = VILLAGES_DATA.features.find(f => f.properties.village.toLowerCase().includes(q));
      if (matchedV) {
        selectVillage(matchedV.properties.id);
      }
    }

    function toggleNavDropdown(e) {
      e.stopPropagation();
      document.getElementById('navDropdownMenu').classList.toggle('show');
    }

    document.addEventListener('click', () => {
      const m = document.getElementById('navDropdownMenu');
      if (m) m.classList.remove('show');
    });
  </script>
</body>
</html>
"""

html_content = html_template.replace('__DISTRICTS_DATA__', districts_json_str)
html_content = html_content.replace('__SUBDISTRICTS_DATA__', subdistricts_json_str)
html_content = html_content.replace('__VILLAGES_DATA__', villages_json_str)
html_content = html_content.replace('__SUMMARY_DATA__', dash_data_json_str)

# Write to both ChiangMai_Water_Triple_Gap_GIS_Dashboard.html and index.html
with open('ChiangMai_Water_Triple_Gap_GIS_Dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully generated ChiangMai_Water_Triple_Gap_GIS_Dashboard.html and index.html (Size: {len(html_content):,} bytes)")
