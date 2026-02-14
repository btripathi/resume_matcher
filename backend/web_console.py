from fastapi.responses import HTMLResponse


def render_console() -> HTMLResponse:
    html = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TalentScout AI</title>
  <style>
    :root {
      --bg: #ffffff;
      --text: #31333f;
      --muted: #6b7280;
      --line: #e5e7eb;
      --card: #ffffff;
      --info-bg: #e8f0fe;
      --info-text: #0b4ea2;
      --active: #ff4b4b;
      --btn: #f7f7f9;
      --ok: #15803d;
      --warn: #b45309;
      --err: #b91c1c;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Source Sans Pro", "Segoe UI", sans-serif;
    }

    .shell {
      max-width: 1120px;
      margin: 0 auto;
      padding: 22px 18px 36px;
    }

    .info {
      background: var(--info-bg);
      color: var(--info-text);
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 17px;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    h1 {
      margin: 0;
      font-size: 56px;
      line-height: 1.04;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .settings-wrap {
      position: relative;
    }
    .settings-btn {
      border: 1px solid #d1d5db;
      background: #fff;
      border-radius: 10px;
      padding: 8px 12px;
      font-size: 15px;
      color: #374151;
      cursor: pointer;
    }
    .settings-menu {
      position: absolute;
      right: 0;
      top: calc(100% + 8px);
      width: min(620px, calc(100vw - 40px));
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
      padding: 10px;
      z-index: 20;
      display: none;
    }
    .settings-menu.open {
      display: block;
    }
    .settings-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      align-items: start;
    }
    .settings-col {
      display: grid;
      gap: 8px;
      align-content: start;
    }
    .settings-item {
      width: 100%;
      text-align: left;
      background: transparent;
      border: none;
      border-radius: 8px;
      padding: 7px 9px;
      color: #334155;
      cursor: pointer;
    }
    .settings-item:hover {
      background: #f8fafc;
    }
    .settings-section {
      border: 1px solid #eef2f7;
      border-radius: 8px;
      padding: 8px;
      margin-bottom: 0;
    }
    .settings-title {
      font-size: 12px;
      font-weight: 700;
      color: #475569;
      margin-bottom: 5px;
    }
    .settings-help {
      font-size: 11px;
      color: #64748b;
      margin-top: 3px;
    }
    .settings-msg {
      font-size: 11px;
      margin-top: 8px;
      color: #0f5132;
    }
    .settings-msg.err {
      color: #991b1b;
    }
    .settings-inline-status {
      border: 1px solid #dbeafe;
      background: #eff6ff;
      color: #1e3a8a;
      border-radius: 8px;
      padding: 7px 8px;
      font-size: 12px;
      line-height: 1.25;
      margin-bottom: 6px;
    }
    .settings-inline-status.ok {
      border-color: #bbf7d0;
      background: #ecfdf3;
      color: #166534;
    }
    .settings-inline-status.warn {
      border-color: #fde68a;
      background: #fffbeb;
      color: #92400e;
    }
    .settings-inline-status.err {
      border-color: #fecaca;
      background: #fef2f2;
      color: #991b1b;
    }
    .settings-action-msg {
      font-size: 12px;
      line-height: 1.3;
      margin-top: 6px;
      color: #166534;
      min-height: 16px;
    }
    .settings-action-msg.err {
      color: #991b1b;
    }

    .tabs {
      display: flex;
      gap: 16px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 14px;
      flex-wrap: wrap;
    }

    .tab {
      appearance: none;
      border: none;
      background: transparent;
      color: #4b5563;
      font-size: 19px;
      padding: 8px 0 10px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
    }

    .tab.active {
      color: var(--active);
      border-color: var(--active);
    }

    .panel, .subpanel { display: none; }
    .panel.active, .subpanel.active { display: block; }

    .subtabs {
      display: flex;
      gap: 14px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 12px;
      flex-wrap: wrap;
    }

    .subtab {
      border: none;
      background: transparent;
      color: #4b5563;
      font-size: 17px;
      padding: 6px 0 8px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
    }

    .subtab.active {
      color: var(--active);
      border-color: var(--active);
    }

    .section { margin-bottom: 16px; }

    .card {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: var(--card);
    }

    h2 {
      margin: 0 0 10px;
      font-size: 31px;
      line-height: 1.16;
      font-weight: 650;
      letter-spacing: -0.01em;
    }

    h3 {
      margin: 0 0 8px;
      font-size: 18px;
      font-weight: 620;
    }

    .caption { color: var(--muted); font-size: 14px; }

    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .row { margin-top: 8px; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
    .row4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; }
    .check-inline { display: flex; align-items: center; gap: 8px; }
    .analysis-options {
      display: grid;
      gap: 8px;
      align-content: start;
    }
    .analysis-actions {
      display: grid;
      grid-template-columns: 1fr minmax(220px, 320px);
      gap: 10px;
      align-items: end;
    }
    .analysis-actions .primary {
      height: 42px;
    }

    input, textarea, select, button {
      width: 100%;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      padding: 9px 11px;
      font-size: 16px;
      font-family: inherit;
      color: var(--text);
      background: #fff;
    }
    input[type="checkbox"],
    input[type="radio"] {
      width: auto;
      border: none;
      border-radius: 0;
      padding: 0;
      margin: 0;
      accent-color: var(--active);
      background: transparent;
    }
    textarea { min-height: 90px; resize: vertical; }
    textarea.json-editor {
      min-height: 200px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      line-height: 1.4;
      background: #fbfdff;
    }
    select[multiple] { min-height: 150px; }
    input[type="range"] {
      accent-color: var(--active);
      padding: 0;
      height: 28px;
      border: 0;
      background: transparent;
    }

    .tab,
    .subtab,
    .settings-btn {
      width: auto;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    button.primary {
      background: var(--active);
      color: #fff;
      border-color: var(--active);
      font-weight: 600;
      cursor: pointer;
    }

    button.secondary {
      background: #fff;
      color: #334155;
      font-weight: 600;
      cursor: pointer;
    }

    button.danger {
      background: #fff;
      color: var(--err);
      border-color: #fecaca;
      font-weight: 600;
      cursor: pointer;
    }

    details.expander {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
      background: #fafafa;
      margin-bottom: 10px;
    }
    details.expander > summary {
      cursor: pointer;
      font-size: 18px;
      line-height: 1.15;
      font-weight: 600;
      color: #374151;
      list-style: none;
    }

    .metrics3 {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin: 14px 0;
    }
    .metrics5 {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
      margin: 14px 0;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px 12px;
      background: #fcfcfd;
    }
    .metric .k {
      color: #475569;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.01em;
      text-transform: uppercase;
    }
    .metric .v {
      font-size: 27px;
      line-height: 1.12;
      margin-top: 8px;
      font-weight: 640;
      color: #0f172a;
    }
    .run-results-panel .section {
      margin-bottom: 20px;
    }
    .actions-menu {
      position: relative;
      width: 220px;
    }
    .actions-menu > summary {
      list-style: none;
      cursor: pointer;
      border: 1px solid #d0d7de;
      border-radius: 10px;
      padding: 10px 12px;
      font-weight: 700;
      color: #334155;
      background: #fff;
      text-align: center;
    }
    .actions-menu > summary::-webkit-details-marker { display: none; }
    .actions-popover {
      position: absolute;
      right: 0;
      top: calc(100% + 6px);
      z-index: 20;
      width: 320px;
      border: 1px solid #d0d7de;
      border-radius: 12px;
      background: #fff;
      padding: 10px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.16);
      display: grid;
      gap: 8px;
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.45);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 2000;
      padding: 20px;
    }
    .modal-backdrop.show { display: flex; }
    .modal-card {
      width: min(520px, 100%);
      border: 1px solid #d0d7de;
      border-radius: 12px;
      background: #fff;
      box-shadow: 0 16px 40px rgba(15, 23, 42, 0.28);
      padding: 14px;
      display: grid;
      gap: 10px;
    }
    .modal-title {
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
    }
    .modal-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .table-wrap {
      border: 1px solid var(--line);
      border-radius: 10px;
      overflow: auto;
      max-height: 380px;
      background: #fff;
    }
    .table-wrap.no-scroll {
      overflow: visible;
      max-height: none;
    }
    table { width: 100%; border-collapse: collapse; }
    th, td {
      text-align: left;
      padding: 8px;
      border-bottom: 1px solid #f1f5f9;
      font-size: 15px;
      vertical-align: top;
    }
    th {
      background: #f8fafc;
      position: sticky;
      top: 0;
      z-index: 1;
      color: #374151;
      font-weight: 600;
    }

    tr:hover td { background: #f9fafb; }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      border: 1px solid #e5e7eb;
    }
    .badge.move { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
    .badge.review { background: #fef3c7; color: #92400e; border-color: #fde68a; }
    .badge.reject { background: #fee2e2; color: #991b1b; border-color: #fecaca; }

    .status { font-size: 12px; font-weight: 700; }
    .status.running { color: var(--warn); }
    .status.failed { color: var(--err); }
    .status.completed { color: var(--ok); }
    .score-sub {
      color: #6b7280;
      font-size: 11px;
      margin-top: 2px;
      display: block;
    }

    .logs {
      border: 1px solid #d1d5db;
      border-radius: 10px;
      min-height: 220px;
      max-height: 320px;
      overflow: auto;
      padding: 8px;
      background: #0f172a;
      color: #dbeafe;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .status-bars {
      display: grid;
      gap: 8px;
      margin-top: 8px;
    }
    .status-bar-card {
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #f8fbff;
      padding: 8px 10px;
    }
    .status-bar-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 6px;
    }
    .status-bar-title {
      font-size: 12px;
      font-weight: 700;
      color: #334155;
      letter-spacing: 0.01em;
      text-transform: uppercase;
    }
    .status-bar-meta {
      font-size: 12px;
      color: #475569;
      white-space: nowrap;
    }
    .status-track {
      height: 8px;
      border-radius: 999px;
      background: #e2e8f0;
      overflow: hidden;
    }
    .status-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #38bdf8, #0284c7);
      transition: width 180ms ease;
    }
    #batchProgressFill {
      background: linear-gradient(90deg, #34d399, #059669);
    }
    .run-health {
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #f8fafc;
      padding: 8px 10px;
      margin-top: 8px;
      display: grid;
      gap: 6px;
    }
    .run-health.stuck {
      border-color: #fecaca;
      background: #fef2f2;
    }
    .run-health-title {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.01em;
      color: #334155;
    }
    .run-health-meta {
      font-size: 13px;
      color: #1f2937;
    }
    .run-health.stuck .run-health-meta {
      color: #991b1b;
      font-weight: 600;
    }
    .run-health-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .run-health-actions button {
      width: auto;
      min-width: 180px;
    }
    .run-stuck-alert {
      display: none;
      margin-top: 8px;
      margin-bottom: 8px;
      border: 1px solid #fecaca;
      background: #fff1f2;
      color: #9f1239;
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 13px;
      line-height: 1.35;
      font-weight: 600;
    }

    .detail {
      border: 1px solid #d1d5db;
      border-radius: 10px;
      min-height: 180px;
      max-height: 330px;
      overflow: auto;
      padding: 8px;
      background: #fbfdff;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .investigator {
      border: none;
      border-radius: 0;
      padding: 0;
      background: transparent;
    }
    #legacyMatchDetail,
    #simpleMatchDetail {
      border: none;
      border-radius: 0;
      min-height: 0;
      max-height: none;
      overflow: visible;
      padding: 0;
      background: transparent;
      font-family: inherit;
      white-space: normal;
    }
    .investigator-head {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 14px;
      margin-bottom: 12px;
      align-items: start;
    }
    .investigator-name {
      font-size: 20px;
      font-weight: 700;
      line-height: 1.25;
    }
    .investigator-score-card {
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 8px 10px;
      min-width: 132px;
      background: #f8fafc;
    }
    .investigator-score {
      font-size: 34px;
      font-weight: 700;
      text-align: right;
      line-height: 1;
    }
    .investigator-controls {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      margin-bottom: 10px;
      align-items: center;
    }
    .investigator-controls button {
      width: auto;
      min-width: 260px;
      justify-self: end;
    }
    .mini-muted { color: #6b7280; font-size: 12px; }
    .final-decision {
      background: #e8f0fe;
      color: #0b4ea2;
      border-radius: 8px;
      padding: 8px 10px;
      margin: 8px 0;
      font-size: 14px;
      font-weight: 600;
    }
    .status-chip {
      display: inline-block;
      border-radius: 8px;
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid #e5e7eb;
    }
    .status-chip.met { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
    .status-chip.partial { background: #fef3c7; color: #92400e; border-color: #fde68a; }
    .status-chip.missing { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
    .tag-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }
    .tag-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: 999px;
      border: 1px solid #fecaca;
      background: #ffeded;
      color: #7f1d1d;
      font-size: 12px;
      font-weight: 600;
    }
    .tag-chip button {
      width: auto;
      border: none;
      background: transparent;
      color: inherit;
      padding: 0;
      font-size: 12px;
      cursor: pointer;
    }
    .tag-manager-grid {
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      gap: 14px;
    }
    .tag-manager-pane {
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 10px;
      background: #fbfdff;
    }
    .tag-pane-title {
      font-size: 14px;
      font-weight: 700;
      color: #334155;
      margin-bottom: 6px;
    }
    .tag-catalog {
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      max-height: 340px;
      overflow: auto;
      margin-top: 8px;
    }
    .tag-catalog-item {
      width: 100%;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
      border: none;
      border-bottom: 1px solid #f1f5f9;
      border-radius: 0;
      background: #fff;
      color: #1f2937;
      padding: 10px 11px;
      cursor: pointer;
      text-align: left;
    }
    .tag-catalog-item:hover {
      background: #f8fafc;
    }
    .tag-catalog-item:last-child {
      border-bottom: none;
    }
    .tag-catalog-name {
      font-size: 14px;
      font-weight: 600;
      line-height: 1.2;
      word-break: break-word;
    }
    .tag-catalog-meta {
      font-size: 12px;
      color: #64748b;
      margin-top: 3px;
      line-height: 1.25;
    }
    .tag-catalog-total {
      font-size: 12px;
      font-weight: 700;
      color: #0f172a;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      padding: 3px 8px;
      white-space: nowrap;
    }
    .tag-action {
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      padding: 10px;
      margin-bottom: 10px;
    }
    .tag-action:last-child {
      margin-bottom: 0;
    }
    .tag-action h4 {
      margin: 0 0 8px;
      font-size: 14px;
      font-weight: 700;
      color: #334155;
    }
    .tag-action.danger-zone {
      border-color: #fecaca;
      background: #fff7f7;
    }
    .verify-snippet mark {
      background: #fef08a;
      color: #1f2937;
      padding: 0 2px;
      border-radius: 3px;
    }
    .verify-list {
      margin: 0;
      padding-left: 18px;
      line-height: 1.45;
      color: #334155;
    }
    .debug-tools {
      margin-top: 14px;
      border: 1px dashed #cbd5e1;
      border-radius: 10px;
      padding: 10px;
      background: #f8fbff;
    }
    .debug-log {
      border: 1px solid #d1d5db;
      border-radius: 8px;
      min-height: 120px;
      max-height: 260px;
      overflow: auto;
      padding: 8px;
      background: #0f172a;
      color: #dbeafe;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      white-space: pre-wrap;
      line-height: 1.4;
    }

    .msg { margin-top: 6px; font-size: 14px; }
    .msg.ok { color: var(--ok); }
    .msg.err { color: var(--err); }
    .upload-block {
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 10px;
      background: #fafcff;
    }
    .upload-title {
      font-size: 14px;
      font-weight: 600;
      color: #334155;
      margin-bottom: 6px;
    }
    .file-picker {
      border: 1px dashed #cbd5e1;
      border-radius: 10px;
      padding: 10px;
      background: #fff;
    }
    .file-list {
      margin-top: 6px;
      font-size: 12px;
      color: #475569;
      line-height: 1.4;
      white-space: pre-wrap;
    }
    .hidden-input {
      display: none;
    }

    @media (max-width: 1100px) {
      h1 { font-size: 40px; }
      .grid2, .grid3, .row2, .row3, .row4, .metrics3, .metrics5 { grid-template-columns: 1fr; }
      .analysis-actions { grid-template-columns: 1fr; }
      .investigator-controls { grid-template-columns: 1fr; }
      .investigator-controls button { width: 100%; min-width: 0; justify-self: stretch; }
      .settings-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="info" id="topReadOnlyInfo">🔒 Read-only mode: changes are local only and will NOT sync to the shared DB. Enable Write Mode to share results.</div>

    <div class="title-row">
      <h2 style="margin:0">🚀 TalentScout: Intelligent Resume Screening</h2>
      <div class="settings-wrap">
        <button class="settings-btn" id="settingsBtn" onclick="toggleSettingsMenu(event)">⚙️ Settings ▾</button>
        <div class="settings-menu" id="settingsMenu">
          <div class="settings-grid">
            <div class="settings-col">
              <div class="settings-section">
                <div class="settings-title">Configuration</div>
                <input id="setLmUrl" placeholder="LM URL" />
                <input id="setApiKey" class="row" placeholder="API Key" />
                <div class="row2 row">
                  <select id="setLmModel">
                    <option value="">Auto-select model</option>
                  </select>
                  <button class="settings-item" onclick="loadSettingsModels()">Load Models</button>
                </div>
                <label class="settings-help check-inline row"><input id="setOcrEnabled" type="checkbox" /> Enable OCR</label>
                <div class="row2 row">
                  <button class="settings-item" onclick="saveSettingsConfig()">Save Config</button>
                  <button class="settings-item" onclick="testSettingsConnection()">Test Connection</button>
                </div>
              </div>
              <div class="settings-section">
                <div class="settings-title">Sync</div>
                <div class="row2">
                  <button class="settings-item" onclick="pushToGithub()">💾 Push to GitHub</button>
                  <button class="settings-item" onclick="pullFromGithub()">📥 Force Pull</button>
                </div>
                <button class="settings-item row" onclick="clearResultsOnly()">🧹 Clear Results Only</button>
                <button class="settings-item row" onclick="resetDatabase()">🗑️ Reset DB</button>
              </div>
            </div>
            <div class="settings-col">
              <div class="settings-section">
                <div class="settings-title">Write Mode</div>
                <div class="settings-inline-status" id="setWriteModeStatus">Checking write mode status...</div>
                <div class="settings-help" id="setWriteLockInfo">Write lock: unknown</div>
                <input id="setWriterName" class="row" placeholder="Writer name" />
                <div class="settings-help" id="setWriterUsersHint"></div>
                <input id="setWriterPassword" class="row" type="password" placeholder="Write password" />
                <div class="row2 row">
                  <button class="settings-item" onclick="enableWriteMode()">Enable Write Mode</button>
                  <button class="settings-item" onclick="disableWriteMode()">Disable / Release Lock</button>
                </div>
                <button class="settings-item row" onclick="forceUnlockWriteMode()">Force Unlock (Admin)</button>
                <div class="settings-action-msg" id="setWriteModeActionMsg"></div>
              </div>
              <div class="settings-section">
                <div class="settings-title">Utilities</div>
                <button class="settings-item" onclick="settingsAction('refresh')">Refresh All Data</button>
              </div>
            </div>
          </div>
          <div class="settings-msg" id="settingsMsg"></div>
        </div>
      </div>
    </div>

    <div class="tabs">
      <button class="tab active" id="tab-results" onclick="switchTop('results')">Match Results</button>
      <button class="tab" id="tab-analysis" onclick="switchTop('analysis')">Run Analysis</button>
      <button class="tab" id="tab-manage" onclick="switchTop('manage')">Manage Data</button>
    </div>

    <section class="panel active" id="panel-results">
      <div class="section" style="margin-bottom:8px;">
        <label class="caption check-inline">
          <input id="resultsSimpleMode" type="checkbox" onchange="toggleResultsMode()" />
          📌 Enable Simple JD View (off = Full Run-Based Results)
        </label>
      </div>

      <div class="subpanel" id="panel-results-simple" style="display:none;">
        <div class="section">
          <label style="font-size:18px; display:block; margin-bottom:6px;">Select Job Description:</label>
          <select id="simpleJobSelect" onchange="renderSimpleResults()"></select>
          <div class="caption" id="simpleResultScope">Showing all saved matches for selected JD.</div>
          <div class="caption">Use the row-level <b>Delete</b> action to remove all historical matches for a specific JD × Resume pair.</div>
        </div>

        <div class="metrics3">
          <div class="metric"><div class="k">Total Matches</div><div class="v" id="simpleTotal">0</div></div>
          <div class="metric"><div class="k">Deep Matches</div><div class="v" id="simpleDeepCount">0</div></div>
          <div class="metric"><div class="k">Standard Only</div><div class="v" id="simpleStdCount">0</div></div>
        </div>

        <div class="section">
          <h3>✨ Deep Matches</h3>
          <div class="table-wrap" id="simpleDeepTable"></div>
        </div>
        <div class="section">
          <h3>🧠 Standard Matches</h3>
          <div class="table-wrap" id="simpleStdTable"></div>
        </div>
        <div class="section row">
          <h3>🔎 Match Evidence Investigator</h3>
          <div class="investigator-controls">
            <select id="simpleEvidenceSelect" onchange="onSimpleEvidenceSelect()"></select>
            <button class="secondary" onclick="queueSimpleSingleRerun()">🔁 Rerun Selected Candidate</button>
          </div>
          <div class="detail" id="simpleMatchDetail">Select a row to inspect.</div>
        </div>
        <div class="section" id="simpleTagMismatchSection" style="display:none;">
          <h3>⚠️ Tag Mismatch Watchlist</h3>
          <div class="caption" id="simpleTagMismatchCaption"></div>
          <div class="table-wrap" id="simpleTagMismatchTable"></div>
        </div>
      </div>

      <div class="subpanel run-results-panel active" id="panel-results-run">
        <div class="section">
          <label style="font-size:18px; display:block; margin-bottom:6px;">Select Run Batch:</label>
          <div class="row2" style="grid-template-columns: 1fr auto; align-items:start;">
            <select id="legacyRunSelect" onchange="loadLegacyRunResults()"></select>
            <details class="actions-menu" id="legacyActionsMenu">
              <summary>Batch Actions ▾</summary>
              <div class="actions-popover">
                <button class="secondary" onclick="renameLegacyRunBatch()">Rename This Batch</button>
                <label class="caption check-inline"><input id="legacyDeleteWithMatches" type="checkbox" /> Also delete matches linked to this batch</label>
                <button class="secondary" onclick="deleteLegacyRunBatch()">Delete This Batch</button>
                <button class="secondary" onclick="downloadLegacyCsv()">📥 Download CSV</button>
                <button class="secondary" onclick="downloadLegacyJson()">🧾 Download JSON</button>
              </div>
            </details>
          </div>
          <div class="caption" id="legacyRunJobsCaption"></div>
        </div>
        <details class="expander">
          <summary>🔄 Rerun this Batch with New Settings</summary>
          <div class="caption row">Re-running will process JDs and resumes linked to this batch with new parameters.</div>
          <div class="row2 row">
            <input id="legacyRerunName" placeholder="Rerun batch name" />
            <div>
              <label class="caption" style="display:block; margin-bottom:4px;">New Deep Match Threshold (%)</label>
              <div class="row2" style="grid-template-columns: 1fr 60px; align-items:center;">
                <input id="legacyRerunThreshold" type="range" min="0" max="100" value="50" oninput="q('legacyRerunThresholdValue').textContent=this.value" />
                <span id="legacyRerunThresholdValue" style="font-weight:700; text-align:right;">50</span>
              </div>
            </div>
          </div>
          <label class="caption row check-inline"><input id="legacyRerunAutoDeep" type="checkbox" checked /> ✨ Auto-Upgrade to Deep Match</label>
          <label class="caption row check-inline"><input id="legacyRerunMatchTags" type="checkbox" /> 🎯 Auto-match based on JD Tags</label>
          <div class="row3 row">
            <label class="caption check-inline"><input id="legacyRerunForcePass1" type="checkbox" /> Force Re-run Pass 1</label>
            <label class="caption check-inline"><input id="legacyRerunForceDeep" type="checkbox" onchange="syncLegacyDeepForce()" /> Force Re-run Deep Scan</label>
            <label class="caption check-inline"><input id="legacyRerunDeepSinglePrompt" type="checkbox" /> 🧪 Single Prompt Deep Scan</label>
          </div>
          <button class="primary row" onclick="queueLegacyBatchRerun()">🚀 Rerun Batch</button>
          <div class="msg" id="msgLegacyRerun"></div>
        </details>
        <div class="caption" id="legacyRunCaption"></div>
        <div class="metrics5 row">
          <div class="metric"><div class="k">Total Matches</div><div class="v" id="runTotal">0</div></div>
          <div class="metric"><div class="k">Deep Matches</div><div class="v" id="runDeepCount">0</div></div>
          <div class="metric"><div class="k">Standard Only</div><div class="v" id="runStdCount">0</div></div>
          <div class="metric"><div class="k">Unique Candidates</div><div class="v" id="runUniqueCandidates">0</div></div>
          <div class="metric"><div class="k">Unique Jobs</div><div class="v" id="runUniqueJobs">0</div></div>
        </div>
        <div class="section">
          <h3 id="legacyDeepHeading">✨ Deep Matches for Selected Run</h3>
          <div class="table-wrap" id="legacyDeepTable"></div>
        </div>
        <div class="section">
          <h3 id="legacyStdHeading">🧠 Standard Matches (Pass 1 Only)</h3>
          <div class="table-wrap" id="legacyStdTable"></div>
        </div>
        <div class="section row">
          <h3>🔎 Match Evidence Investigator</h3>
          <div class="investigator-controls">
            <select id="legacySingleRerunMatch" onchange="onLegacyCandidateSelect()"></select>
            <button class="secondary" onclick="queueLegacySingleRerun()">🔁 Rerun Selected Candidate</button>
          </div>
          <div class="detail" id="legacyMatchDetail">Select a row to inspect.</div>
        </div>
      </div>
    </section>

    <section class="panel" id="panel-analysis">
      <div class="grid2 section">
        <div>
          <h3>1. Select Job(s)</h3>
          <select id="matchJobSelect" onchange="onAnalysisSelectionChange()"></select>
        </div>
        <div>
          <h3>2. Select Resumes</h3>
          <select id="matchResumeSelect" onchange="onAnalysisSelectionChange()"></select>
        </div>
      </div>
      <div class="row2 section">
        <div>
          <label class="caption" style="display:block; margin-bottom:6px;">Filter by JD Tag (Optional):</label>
          <select id="analysisTagFilter" onchange="applyAnalysisTagFilter()"></select>
        </div>
        <div>
          <label class="caption" style="display:block; margin-bottom:6px;">Run Name</label>
          <input id="runName" placeholder="Run Name" />
        </div>
      </div>
      <div class="row4 section">
        <label class="caption check-inline">
          <input id="analysisAutoTagMatch" type="checkbox" checked onchange="onAnalysisSelectionChange()" />
          🎯 Auto-match based on JD Tags
        </label>
        <label class="caption check-inline">
          <input id="autoDeep" type="checkbox" checked />
          ✨ Auto-Upgrade to Deep Match
        </label>
        <label class="caption check-inline"><input id="forceRerunPass1" type="checkbox" /> Force Re-run Pass 1</label>
        <label class="caption check-inline"><input id="forceRerunDeep" type="checkbox" onchange="syncAnalysisDeepForce()" /> Force Re-run Deep Scan</label>
        <label class="caption check-inline"><input id="deepSinglePrompt" type="checkbox" /> 🧪 Single Prompt Deep Scan</label>
        <label class="caption check-inline"><input id="debugBulkLog" type="checkbox" /> 🐞 Keep Bulk Debug File</label>
      </div>
      <div class="caption section">
        <div id="selectedCountJd">Selected JDs: 0 / 0</div>
        <div id="selectedCountRes">Selected Resumes: 0 / 0</div>
      </div>

      <div class="card section">
        <h3>⚙️ Smart Match Configuration</h3>
        <div class="analysis-actions">
          <div>
            <label class="caption" style="display:block; margin-bottom:4px;">Deep Match Threshold (%)</label>
            <div class="row2" style="grid-template-columns: 1fr 60px; align-items:center;">
              <input id="threshold" type="range" min="0" max="100" value="50" oninput="q('thresholdValue').textContent=this.value" />
              <span id="thresholdValue" style="font-weight:700; text-align:right;">50</span>
            </div>
            <div class="row2" style="margin-top:6px; align-items:center;">
              <label class="caption" for="maxDeepPerJdInput">Max Deep-Scans per JD (0 = unlimited)</label>
              <input id="maxDeepPerJdInput" type="number" min="0" step="1" value="0" />
            </div>
            <div class="row2" style="margin-top:6px; align-items:center;">
              <label class="caption" for="aiConcurrencyInput">AI Request Concurrency (1 = sequential)</label>
              <input id="aiConcurrencyInput" type="number" min="1" max="32" step="1" value="1" />
            </div>
            <div class="row2" style="margin-top:6px; align-items:center;">
              <label class="caption" for="jobConcurrencyInput">Queue Job Concurrency (parallel resumes)</label>
              <input id="jobConcurrencyInput" type="number" min="1" max="32" step="1" value="1" />
            </div>
          </div>
          <button class="primary" id="startAnalysisBtn" onclick="queueScoreMatch()">🚀 START ANALYSIS</button>
        </div>
        <div class="msg" id="msgMatch"></div>
      </div>

      <div class="card">
        <h3>Live Run Logs</h3>
        <div class="caption" id="runCounts">No active queue jobs.</div>
        <div class="run-stuck-alert" id="runStuckAlert"></div>
        <div class="run-health" id="runHealthBox">
          <div class="run-health-title">Selected Run Status</div>
          <div class="run-health-meta" id="runHealthMeta">No active run selected.</div>
          <div class="run-health-actions">
            <button class="danger" id="resumeRunBtn" style="display:none;" onclick="resumeSelectedRun()">Resume Stuck Run</button>
            <button class="secondary" id="pauseRunBtn" style="display:none;" onclick="pauseSelectedRun()">Pause Run</button>
            <button class="secondary" id="skipCurrentBtn" style="display:none;" onclick="skipCurrentRun()">⏭ Skip Current Job</button>
            <button class="danger" id="cancelRunBtn" style="display:none;" onclick="cancelSelectedRun()">Stop &amp; Clean Run</button>
            <button class="danger" id="cancelBatchBtn" style="display:none;" onclick="cancelWholeBatch()">🛑 Stop Whole Batch</button>
          </div>
        </div>
        <div class="status-bars">
          <div class="status-bar-card">
            <div class="status-bar-head">
              <div class="status-bar-title" id="jobProgressLabel">Current Job</div>
              <div class="status-bar-meta" id="jobProgressMeta">0%</div>
            </div>
            <div class="status-track"><div class="status-fill" id="jobProgressFill"></div></div>
          </div>
          <div class="status-bar-card">
            <div class="status-bar-head">
              <div class="status-bar-title" id="batchProgressLabel">Batch Progress</div>
              <div class="status-bar-meta" id="batchProgressMeta">0/0 complete</div>
            </div>
            <div class="status-track"><div class="status-fill" id="batchProgressFill"></div></div>
          </div>
        </div>
        <div class="row2 row">
          <select id="selectedRunId" onchange="onActiveRunSelection()"></select>
          <button class="secondary" onclick="refreshRunPanels()">Refresh Runs & Logs</button>
        </div>
        <div class="logs row" id="runLogs">No active run selected.</div>
        <details class="expander row">
          <summary>History Runs (Completed / Failed / Canceled)</summary>
          <div class="row2 row">
            <select id="historyRunId" onchange="onHistoryRunSelection()"></select>
            <button class="secondary" onclick="loadHistoryLogs()">View Selected History Log</button>
          </div>
          <div class="caption row">Use this dropdown to inspect completed or failed runs.</div>
        </details>
      </div>
    </section>

    <section class="panel" id="panel-manage">
      <div class="subtabs">
        <button class="subtab active" id="sub-manage-upload" onclick="switchManage('upload')">📤 Data Upload</button>
        <button class="subtab" id="sub-manage-data" onclick="switchManage('data')">🗂️ Data Manager</button>
      </div>

      <details class="expander row manage-upload-section" id="autoUploadSection" open>
        <summary>🪄 Auto-detect Uploads (JD / Resume)</summary>
        <div class="caption row">Upload mixed documents once. The app auto-classifies each file as Job Description or Resume.</div>
        <div class="upload-block row">
          <div class="upload-title">Assign Tag(s) to Uploaded Documents (Optional)</div>
          <div class="row2">
            <select id="autoTagAssign"></select>
            <button class="secondary" onclick="addAutoUploadTag()">Add Selected Tag</button>
          </div>
          <div class="row2 row">
            <input id="newAutoTagName" placeholder="Create new tag (optional)" />
            <button class="secondary" onclick="addInlineTagToSelect('newAutoTagName','autoTagAssign','msgAutoUpload')">Create & Add Tag</button>
          </div>
          <input id="autoTagsCsv" class="hidden-input" />
          <div class="tag-chips" id="autoUploadTagChips"></div>
        </div>
        <div class="upload-block row">
          <div class="upload-title">Upload Documents (PDF/DOCX/TXT)</div>
          <div class="file-picker">
            <input class="row" id="autoFileUpload" type="file" multiple accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onchange="updateUploadFileInfo('autoFileUpload','autoUploadFilesInfo')" />
            <div class="file-list" id="autoUploadFilesInfo">No files selected.</div>
          </div>
          <label class="caption row check-inline"><input id="autoForceReparse" type="checkbox" /> Force Reparse Existing Files</label>
        </div>
        <button class="primary row" id="autoUploadBtn" onclick="queueIngestAuto()">Process Documents (Auto-detect)</button>
        <div class="detail row" id="autoUploadLive">No active auto-detect upload runs.</div>
        <div class="table-wrap no-scroll row" id="autoUploadResultsTable"></div>
        <div class="msg" id="msgAutoUpload"></div>
      </details>

      <div class="card row manage-data-section" id="unifiedDataBrowser" style="display:none;">
        <h3>Document Browser</h3>
        <div class="caption">Select type, filter by tag, then click a row to open details below.</div>
        <div class="row3 row">
          <select id="manageEntityType" onchange="renderUnifiedDataBrowser()">
            <option value="all" selected>All Documents</option>
            <option value="job">Job Descriptions</option>
            <option value="resume">Resumes</option>
          </select>
          <select id="manageEntityTag" onchange="renderUnifiedDataBrowser()"></select>
          <input id="manageEntitySearch" placeholder="Search filename..." oninput="renderUnifiedDataBrowser()" />
        </div>
        <div class="table-wrap no-scroll row" id="manageEntityTable"></div>
        <div class="row2 row">
          <select id="manageEntitySelect" onchange="openUnifiedDataRecord()"></select>
          <div class="caption" id="manageEntityCount">0 items</div>
        </div>
      </div>
      <div class="card row manage-data-section" id="unifiedDataEditor" style="display:none;">
        <h3 id="unifiedEditTitle">Document Details</h3>
        <div class="row" id="unifiedEditingLabel" style="font-weight:600;">Editing: none selected</div>
        <details class="expander row">
          <summary>🔍 Inspect Raw Extracted Text</summary>
          <div class="detail" id="unifiedRaw"></div>
        </details>
        <h3>Edit Tags</h3>
        <div class="row2">
          <select id="unifiedTagSelect"></select>
          <button class="secondary" onclick="addUnifiedEditTag()">Add Tag</button>
        </div>
        <input class="row" id="unifiedTagsCsv" placeholder="Selected tags (comma separated)" oninput="renderUnifiedEditTagChips()" />
        <div class="tag-chips" id="unifiedEditTagChips"></div>
        <h3 class="row" id="unifiedJsonHeading">JSON</h3>
        <textarea class="row json-editor" id="unifiedJsonEditor" placeholder="JSON"></textarea>
        <div class="row2 row">
          <button class="secondary" onclick="formatJsonEditor('unifiedJsonEditor','msgUnifiedEdit')">Format JSON</button>
          <button class="secondary" onclick="validateJsonEditor('unifiedJsonEditor','msgUnifiedEdit')">Validate JSON</button>
        </div>
        <div class="row3 row">
          <button class="secondary" onclick="reprocessUnifiedRecord()">Reprocess</button>
          <button class="primary" onclick="saveUnifiedRecord()">Save Changes</button>
          <button class="danger" onclick="deleteUnifiedRecord()">Delete</button>
        </div>
        <div class="msg" id="msgUnifiedEdit"></div>
      </div>

      <div class="subpanel active" id="panel-manage-jd">
        <details class="expander manage-upload-section">
          <summary>♻️ Reparse Existing JDs</summary>
          <div class="row2 row">
            <select id="reparseJdScope" onchange="toggleReparseJDSelection()">
              <option value="all">All JDs</option>
              <option value="selected">Selected JDs</option>
            </select>
            <input id="reparseJdSearch" placeholder="Search JDs" oninput="filterReparseJDs()" />
          </div>
          <select id="reparseJdSelect" class="row" multiple></select>
          <div class="row">
            <button class="secondary" onclick="reparseJD()">Reparse JDs Now</button>
          </div>
          <div class="msg" id="msgReparseJD"></div>
        </details>

        <details class="expander manage-upload-section">
          <summary>📤 Upload New Job Descriptions</summary>
          <div class="upload-block row">
            <div class="upload-title">Assign Tag(s) to JDs</div>
            <div class="row2">
              <select id="jdTagAssign"></select>
              <button class="secondary" onclick="addJdUploadTag()">Add Selected Tag</button>
            </div>
            <div class="row2 row">
              <input id="newJdTagName" placeholder="Create new tag (optional)" />
              <button class="secondary" onclick="addInlineTagToSelect('newJdTagName','jdTagAssign','msgJD')">Create & Add Tag</button>
            </div>
            <input id="jdTagsCsv" class="hidden-input" />
            <div class="tag-chips" id="jdUploadTagChips"></div>
          </div>
          <div class="upload-block row">
            <div class="upload-title">Upload JDs (PDF/DOCX/TXT)</div>
            <div class="file-picker">
              <input class="row" id="jdFileUpload" type="file" multiple accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onchange="updateUploadFileInfo('jdFileUpload','jdUploadFilesInfo')" />
              <div class="file-list" id="jdUploadFilesInfo">No files selected.</div>
            </div>
            <label class="caption row check-inline"><input id="jdForceReparse" type="checkbox" /> Force Reparse Existing JDs</label>
          </div>
          <button class="primary row" onclick="queueIngestJob()">Process New JDs</button>
          <div class="msg" id="msgJD"></div>
        </details>

        <div class="card legacy-manager-section" style="display:none;">
          <h3>Manage JDs</h3>
          <div class="caption" id="jdCount">Use Document Browser above to select a JD.</div>
          <div class="row" id="jdEditingLabel" style="font-weight:600;"></div>
          <details class="expander row">
            <summary>🔍 Inspect Raw Extracted Text</summary>
            <div class="detail" id="jdRaw"></div>
          </details>
          <h3>Edit JD Tags</h3>
          <div class="row2">
            <select id="editJdTagSelect"></select>
            <button class="secondary" onclick="addEditJdTag()">Add Tag</button>
          </div>
          <input class="row" id="editJdTagsCsv" placeholder="Selected JD tags (comma separated)" oninput="renderEditJdTagChips()" />
          <div class="tag-chips" id="editJdTagChips"></div>
          <h3 class="row">JSON Criteria</h3>
          <textarea class="row json-editor" id="editJdCriteria" placeholder="JSON Criteria"></textarea>
          <div class="row2 row">
            <button class="secondary" onclick="formatJsonEditor('editJdCriteria','msgEditJD')">Format JSON</button>
            <button class="secondary" onclick="validateJsonEditor('editJdCriteria','msgEditJD')">Validate JSON</button>
          </div>
          <div class="row2 row">
            <button class="primary" onclick="saveJD()">Save JD Changes</button>
            <button class="danger" onclick="deleteJD()">Delete JD</button>
          </div>
          <div class="msg" id="msgEditJD"></div>
        </div>
      </div>

      <div class="subpanel" id="panel-manage-res">
        <details class="expander manage-upload-section">
          <summary>♻️ Reparse Existing Resumes</summary>
          <div class="row2 row">
            <select id="reparseResScope" onchange="toggleReparseResSelection()">
              <option value="all">All Resumes</option>
              <option value="selected">Selected Resumes</option>
            </select>
            <input id="reparseResSearch" placeholder="Search Resumes" oninput="filterReparseResumes()" />
          </div>
          <select id="reparseResSelect" class="row" multiple></select>
          <div class="row">
            <button class="secondary" onclick="reparseResume()">Reparse Resumes Now</button>
          </div>
          <div class="msg" id="msgReparseRes"></div>
        </details>

        <details class="expander manage-upload-section">
          <summary>📤 Upload / Import Resumes</summary>
          <div class="upload-block row">
            <div class="upload-title">Assign Tag(s) to Resumes</div>
            <div class="row2">
              <select id="resTagAssign"></select>
              <button class="secondary" onclick="addResUploadTag()">Add Selected Tag</button>
            </div>
            <div class="row2 row">
              <input id="newResTagName" placeholder="Create new tag (optional)" />
              <button class="secondary" onclick="addInlineTagToSelect('newResTagName','resTagAssign','msgRes')">Create & Add Tag</button>
            </div>
            <input id="resTagsCsv" class="hidden-input" />
            <div class="tag-chips" id="resUploadTagChips"></div>
          </div>
          <div class="upload-block row">
            <div class="upload-title">Upload Resumes (PDF/DOCX/TXT)</div>
            <div class="file-picker">
              <input class="row" id="resFileUpload" type="file" multiple accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onchange="updateUploadFileInfo('resFileUpload','resUploadFilesInfo')" />
              <div class="file-list" id="resUploadFilesInfo">No files selected.</div>
            </div>
            <label class="caption row check-inline"><input id="resForceReparse" type="checkbox" /> Force Reparse Existing Resumes</label>
          </div>
          <button class="primary row" onclick="queueIngestResume()">Process New Resumes</button>
          <div class="upload-block row">
            <div class="upload-title">Bulk JSON Import</div>
            <input class="row" id="resJsonImport" type="file" accept=".json,application/json" />
            <button class="secondary row" onclick="importResumeJson()">📥 Import JSON Data</button>
          </div>
          <div class="msg" id="msgRes"></div>
        </details>

        <div class="card legacy-manager-section" style="display:none;">
          <h3>Manage Resumes</h3>
          <div class="row2">
            <select id="resTagFilter" onchange="renderResumes()"></select>
            <div class="caption" id="resCount">Use Document Browser above to select a Resume.</div>
          </div>
          <div class="row" id="resEditingLabel" style="font-weight:600;"></div>
          <details class="expander row">
            <summary>🔍 Inspect Raw Extracted Text</summary>
            <div class="detail" id="resRaw"></div>
          </details>
          <h3>Edit Resume Tags</h3>
          <div class="row2">
            <select id="editResTagSelect"></select>
            <button class="secondary" onclick="addEditResTag()">Add Tag</button>
          </div>
          <input class="row" id="editResTagsCsv" placeholder="Selected resume tags (comma separated)" oninput="renderEditResTagChips()" />
          <div class="tag-chips" id="editResTagChips"></div>
          <h3 class="row">JSON Profile</h3>
          <textarea class="row json-editor" id="editResProfile" placeholder="JSON Profile"></textarea>
          <div class="row2 row">
            <button class="secondary" onclick="formatJsonEditor('editResProfile','msgEditRes')">Format JSON</button>
            <button class="secondary" onclick="validateJsonEditor('editResProfile','msgEditRes')">Validate JSON</button>
          </div>
          <div class="row2 row">
            <button class="primary" onclick="saveResume()">Save Profile & Tags</button>
            <button class="danger" onclick="deleteResume()">Delete Resume</button>
          </div>
          <div class="msg" id="msgEditRes"></div>
        </div>
      </div>

      <div class="subpanel" id="panel-manage-tags">
        <div class="card">
          <details class="expander manage-data-section" style="display:none;">
            <summary>🏷️ Tag Manager</summary>
            <div>
          <h3>Tag Manager</h3>
          <div class="caption" id="tagCount">Total Tags: 0</div>
          <div class="tag-manager-grid row">
            <div class="tag-manager-pane">
              <div class="tag-pane-title">Tag Directory</div>
              <div class="caption">Click a tag to prefill rename/delete actions.</div>
              <input class="row" id="tagSearch" placeholder="Search tags..." oninput="renderTagCatalog()" />
              <div class="tag-catalog" id="tagCatalog"></div>
            </div>
            <div class="tag-manager-pane">
              <div class="tag-action">
                <h4>Create Tag</h4>
                <div class="row2">
                  <input id="newTag" placeholder="New tag name" />
                  <button class="primary" onclick="addTag()">Add Tag</button>
                </div>
              </div>
              <div class="tag-action">
                <h4>Rename Tag</h4>
                <div class="row2">
                  <select id="renameTagOld" onchange="prefillRenameTag()"></select>
                  <input id="renameTagNew" placeholder="New name" />
                </div>
                <div class="caption row" id="renameTagImpact">Select a tag to rename.</div>
                <button class="secondary row" onclick="renameTag()">Rename Tag</button>
              </div>
              <div class="tag-action danger-zone">
                <h4>Delete Tag</h4>
                <div class="row2">
                  <select id="deleteTagSel" onchange="updateDeleteTagImpact()"></select>
                  <button class="danger" onclick="deleteTag()">Delete Tag</button>
                </div>
                <div class="caption row" id="deleteTagImpact">Select a tag to see impact.</div>
              </div>
            </div>
          </div>
          <div class="msg" id="msgTag"></div>
            </div>
          </details>
        </div>
      </div>

      <div class="subpanel" id="panel-manage-verify">
        <div class="card manage-data-section" style="display:none;">
          <h3>Data Verification</h3>
          <div class="caption" id="verifyContext">Select a document from Document Browser to load verification details.</div>
          <div class="row3 row" style="display:none;">
            <select id="verifyMode" onchange="renderVerifySelectors()">
              <option value="job">Job Description</option>
              <option value="resume">Resume</option>
            </select>
            <select id="verifyTagFilter" onchange="renderVerifySelectors()"></select>
            <select id="verifyItem" onchange="loadVerifyItem()"></select>
          </div>
              <div class="grid2 row">
                <div>
                  <h3>Extracted Text</h3>
                  <div class="detail" id="verifyRaw"></div>
                </div>
            <div>
              <h3>Parsed JSON</h3>
                  <div class="detail" id="verifyJson"></div>
                </div>
              </div>
              <div class="row2 row">
                <select id="verifyEvidenceTarget" onchange="runEvidenceCheck()"></select>
                <button class="secondary" onclick="runEvidenceCheck()">Evidence Check</button>
              </div>
              <div class="detail verify-snippet row" id="verifyEvidence">Select an item to inspect evidence.</div>
              <h3 class="row">Paste sentence to find matching items</h3>
              <div class="row2">
                <input id="verifyQuery" placeholder="Sentence or phrase" />
                <button class="secondary" onclick="runVerifySimilarity()">Find Closest Items</button>
              </div>
              <div class="detail row" id="verifyClosest">No query yet.</div>
              <h3 class="row">Verification Results</h3>
              <div class="table-wrap no-scroll row" id="verifyTable"></div>
              <details class="expander row">
                <summary>🛠️ Debug Tools</summary>
                <div class="debug-tools">
                  <div class="row2">
                    <button class="secondary" onclick="runDebugHealthCheck()">Run Health Check</button>
                    <button class="secondary" onclick="copyDebugLog()">Copy Debug Log</button>
                  </div>
                  <div class="caption row">Recent client-side errors and API failures appear here.</div>
                  <div class="debug-log row" id="debugLog">Diagnostics ready.</div>
                </div>
              </details>
            </div>
      </div>
    </section>
  </div>
  <div class="modal-backdrop" id="textPromptModal" onclick="onTextPromptBackdropClick(event)">
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="textPromptTitle">
      <div class="modal-title" id="textPromptTitle">Rename</div>
      <label class="caption" id="textPromptLabel" for="textPromptInput">Name</label>
      <input id="textPromptInput" />
      <div class="modal-actions">
        <button class="secondary" onclick="closeTextPrompt(null)">Cancel</button>
        <button class="primary" id="textPromptConfirm" onclick="confirmTextPrompt()">Save</button>
      </div>
    </div>
  </div>
  <div class="modal-backdrop" id="confirmModal" onclick="onConfirmBackdropClick(event)">
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="confirmTitle">
      <div class="modal-title" id="confirmTitle">Confirm Action</div>
      <div class="caption" id="confirmMessage">Are you sure?</div>
      <div class="modal-actions">
        <button class="secondary" onclick="closeConfirmModal(false)">Cancel</button>
        <button class="primary" id="confirmOkBtn" onclick="closeConfirmModal(true)">Confirm</button>
      </div>
    </div>
  </div>

<script>
  const state = {
    jobs: [], resumes: [], tags: [], matches: [], runs: [], legacyRuns: [], legacyRunResults: [], verifyData: null,
    verifyItems: [],
    selectedLegacyRunId: null,
    selectedLegacyMatchId: null,
    selectedSimpleMatchId: null,
    lastAutoRunName: null,
    analysisQueuedRunIds: [],
    analysisAutoPollEnabled: false,
    analysisSubmitting: false,
    autoUploadSubmitting: false,
    autoUploadRunIds: [],
    pauseSettleRunId: null,
    queuePauseActionInFlight: false,
    logPinnedRunId: null,
    settings: null,
    selectedEditJdId: null,
    selectedEditResId: null,
    selectedUnifiedType: null,
    selectedUnifiedId: null,
    reprocessRunId: null,
    logAutoFollow: true,
    lastLoadedLogRunId: null,
  };

  const q = (id) => document.getElementById(id);
  const tagsFrom = (s) => String(s || '').split(',').map(x => x.trim()).filter(Boolean);
  const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const DEBUG_LOG_LIMIT = 300;
  const ANALYSIS_BATCH_STORAGE_KEY = 'talentscout.analysisQueuedRunIds';
  const debugLines = [];
  let textPromptResolver = null;
  let confirmModalResolver = null;

  function loadPersistedBatchRunIds() {
    try {
      const raw = localStorage.getItem(ANALYSIS_BATCH_STORAGE_KEY);
      if (!raw) return [];
      const arr = JSON.parse(raw);
      if (!Array.isArray(arr)) return [];
      return Array.from(new Set(arr.map((x) => Number(x)).filter(Boolean)));
    } catch {
      return [];
    }
  }

  function persistBatchRunIds(ids) {
    try {
      const clean = Array.from(new Set((ids || []).map((x) => Number(x)).filter(Boolean)));
      if (!clean.length) {
        localStorage.removeItem(ANALYSIS_BATCH_STORAGE_KEY);
        return;
      }
      localStorage.setItem(ANALYSIS_BATCH_STORAGE_KEY, JSON.stringify(clean));
    } catch {
      // Ignore storage failures.
    }
  }

  function setTrackedBatchRunIds(ids) {
    state.analysisQueuedRunIds = Array.from(new Set((ids || []).map((x) => Number(x)).filter(Boolean)));
    persistBatchRunIds(state.analysisQueuedRunIds);
  }

  function clearTrackedBatchRunIds() {
    state.analysisQueuedRunIds = [];
    persistBatchRunIds([]);
  }

  function isQueuePausedByRuns(runs = null) {
    const rows = Array.isArray(runs) ? runs : (state.runs || []);
    return rows.some((r) => String(r && r.status ? r.status : '') === 'paused' || isPauseRequested(r));
  }

  function hasLiveQueueRuns(runs = null) {
    const rows = Array.isArray(runs) ? runs : (state.runs || []);
    if (isQueuePausedByRuns(rows)) return false;
    return rows.some((r) => {
      const status = String(r && r.status ? r.status : '');
      if (status === 'queued') return true;
      if (status === 'running' && !isPauseRequested(r)) return true;
      return false;
    });
  }

  function debugLog(message, level = 'info') {
    const line = `[${new Date().toISOString()}] [${String(level || 'info').toUpperCase()}] ${String(message || '')}`;
    debugLines.push(line);
    if (debugLines.length > DEBUG_LOG_LIMIT) debugLines.shift();
    const el = q('debugLog');
    if (el) {
      el.textContent = debugLines.join('\\n');
      el.scrollTop = el.scrollHeight;
    }
    if (level === 'error') console.error(line);
    else if (level === 'warn') console.warn(line);
    else console.log(line);
  }

  window.addEventListener('error', (e) => {
    const msg = `JS error: ${e.message || 'unknown'} @ ${e.filename || 'inline'}:${e.lineno || 0}:${e.colno || 0}`;
    debugLog(msg, 'error');
  });

  window.addEventListener('unhandledrejection', (e) => {
    const reason = e && e.reason ? (e.reason.message || String(e.reason)) : 'unknown';
    debugLog(`Unhandled promise rejection: ${reason}`, 'error');
  });

  async function getJson(url) {
    const r = await fetch(url);
    const d = await r.json();
    if (!r.ok) {
      const msg = d.detail || `HTTP ${r.status}`;
      debugLog(`GET ${url} failed: ${msg}`, 'error');
      throw new Error(msg);
    }
    return d;
  }

  async function send(url, method = 'POST', body = null) {
    const r = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : null,
    });
    let d = {};
    try { d = await r.json(); } catch (e) {}
    if (!r.ok) {
      const msg = d.detail || `HTTP ${r.status}`;
      debugLog(`${method} ${url} failed: ${msg}`, 'error');
      throw new Error(msg);
    }
    return d;
  }

  function setMsg(id, text, ok = true) {
    const el = q(id);
    if (!el) return;
    el.className = `msg ${ok ? 'ok' : 'err'}`;
    el.textContent = text;
    if (!ok && text) debugLog(`${id}: ${text}`, 'warn');
  }

  function parseJsonText(raw) {
    const text = String(raw || '').trim();
    if (!text) return {};
    return JSON.parse(text);
  }

  function getMultiSelectValues(id) {
    const el = q(id);
    if (!el) return [];
    return Array.from(el.selectedOptions || []).map((o) => String(o.value)).filter(Boolean);
  }

  function setMultiSelectValues(id, values) {
    const el = q(id);
    if (!el) return;
    const wanted = new Set((values || []).map((v) => String(v)));
    Array.from(el.options || []).forEach((o) => {
      o.selected = wanted.has(String(o.value));
    });
  }

  function addEditJdTag() {
    const sel = q('editJdTagSelect');
    const tag = String((sel && sel.value) || '').trim();
    if (!tag) return;
    const tags = tagsFrom(q('editJdTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('editJdTagsCsv').value = tags.join(', ');
    renderEditJdTagChips();
  }

  function addUnifiedEditTag() {
    const tag = String((q('unifiedTagSelect') && q('unifiedTagSelect').value) || '').trim();
    if (!tag) return;
    const tags = tagsFrom(q('unifiedTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('unifiedTagsCsv').value = tags.join(', ');
    renderUnifiedEditTagChips();
  }

  function removeUnifiedEditTag(tag) {
    const tags = tagsFrom(q('unifiedTagsCsv').value).filter((t) => t !== tag);
    q('unifiedTagsCsv').value = tags.join(', ');
    renderUnifiedEditTagChips();
  }

  function renderUnifiedEditTagChips() {
    const wrap = q('unifiedEditTagChips');
    if (!wrap) return;
    const tags = tagsFrom(q('unifiedTagsCsv').value);
    if (!tags.length) {
      wrap.innerHTML = '<span class="caption">No tags assigned.</span>';
      return;
    }
    wrap.innerHTML = tags
      .map((t) => `<span class="tag-chip">${t}<button type="button" onclick='removeUnifiedEditTag(${JSON.stringify(String(t))})'>✕</button></span>`)
      .join('');
  }

  function addJdUploadTag() {
    const tag = String((q('jdTagAssign').value || '')).trim();
    if (!tag) return;
    const tags = tagsFrom(q('jdTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('jdTagsCsv').value = tags.join(', ');
    renderJdUploadTagChips();
  }

  function addAutoUploadTag() {
    const tag = String((q('autoTagAssign').value || '')).trim();
    if (!tag) return;
    const tags = tagsFrom(q('autoTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('autoTagsCsv').value = tags.join(', ');
    renderAutoUploadTagChips();
  }

  function removeAutoUploadTag(tag) {
    const tags = tagsFrom(q('autoTagsCsv').value).filter((t) => t !== tag);
    q('autoTagsCsv').value = tags.join(', ');
    renderAutoUploadTagChips();
  }

  function renderAutoUploadTagChips() {
    const wrap = q('autoUploadTagChips');
    if (!wrap) return;
    const tags = tagsFrom(q('autoTagsCsv').value);
    if (!tags.length) {
      wrap.innerHTML = '<span class="caption">No tags assigned.</span>';
      return;
    }
    wrap.innerHTML = tags
      .map((t) => `<span class="tag-chip">${t}<button type="button" onclick='removeAutoUploadTag(${JSON.stringify(String(t))})'>✕</button></span>`)
      .join('');
  }

  function removeJdUploadTag(tag) {
    const tags = tagsFrom(q('jdTagsCsv').value).filter((t) => t !== tag);
    q('jdTagsCsv').value = tags.join(', ');
    renderJdUploadTagChips();
  }

  function renderJdUploadTagChips() {
    const wrap = q('jdUploadTagChips');
    if (!wrap) return;
    const tags = tagsFrom(q('jdTagsCsv').value);
    if (!tags.length) {
      wrap.innerHTML = '<span class="caption">No tags assigned.</span>';
      return;
    }
    wrap.innerHTML = tags
      .map((t) => `<span class="tag-chip">${t}<button type="button" onclick='removeJdUploadTag(${JSON.stringify(String(t))})'>✕</button></span>`)
      .join('');
  }

  function updateUploadFileInfo(fileInputId, infoId) {
    const input = q(fileInputId);
    const info = q(infoId);
    if (!input || !info) return;
    const files = Array.from(input.files || []);
    if (!files.length) {
      info.textContent = 'No files selected.';
      return;
    }
    const names = files.map((f) => f.name);
    info.textContent = `${files.length} file(s) selected:\n${names.join('\n')}`;
  }

  function addResUploadTag() {
    const tag = String((q('resTagAssign').value || '')).trim();
    if (!tag) return;
    const tags = tagsFrom(q('resTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('resTagsCsv').value = tags.join(', ');
    renderResUploadTagChips();
  }

  function removeResUploadTag(tag) {
    const tags = tagsFrom(q('resTagsCsv').value).filter((t) => t !== tag);
    q('resTagsCsv').value = tags.join(', ');
    renderResUploadTagChips();
  }

  function renderResUploadTagChips() {
    const wrap = q('resUploadTagChips');
    if (!wrap) return;
    const tags = tagsFrom(q('resTagsCsv').value);
    if (!tags.length) {
      wrap.innerHTML = '<span class="caption">No tags assigned.</span>';
      return;
    }
    wrap.innerHTML = tags
      .map((t) => `<span class="tag-chip">${t}<button type="button" onclick='removeResUploadTag(${JSON.stringify(String(t))})'>✕</button></span>`)
      .join('');
  }

  function removeEditJdTag(tag) {
    const tags = tagsFrom(q('editJdTagsCsv').value).filter((t) => t !== tag);
    q('editJdTagsCsv').value = tags.join(', ');
    renderEditJdTagChips();
  }

  function renderEditJdTagChips() {
    const wrap = q('editJdTagChips');
    if (!wrap) return;
    const tags = tagsFrom(q('editJdTagsCsv').value);
    if (!tags.length) {
      wrap.innerHTML = '<span class="caption">No tags attached.</span>';
      return;
    }
    wrap.innerHTML = tags
      .map((t) => `<span class="tag-chip">${t}<button type="button" onclick='removeEditJdTag(${JSON.stringify(String(t))})'>✕</button></span>`)
      .join('');
  }

  function addEditResTag() {
    const sel = q('editResTagSelect');
    const tag = String((sel && sel.value) || '').trim();
    if (!tag) return;
    const tags = tagsFrom(q('editResTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('editResTagsCsv').value = tags.join(', ');
    renderEditResTagChips();
  }

  function removeEditResTag(tag) {
    const tags = tagsFrom(q('editResTagsCsv').value).filter((t) => t !== tag);
    q('editResTagsCsv').value = tags.join(', ');
    renderEditResTagChips();
  }

  function renderEditResTagChips() {
    const wrap = q('editResTagChips');
    if (!wrap) return;
    const tags = tagsFrom(q('editResTagsCsv').value);
    if (!tags.length) {
      wrap.innerHTML = '<span class="caption">No tags attached.</span>';
      return;
    }
    wrap.innerHTML = tags
      .map((t) => `<span class="tag-chip">${t}<button type="button" onclick='removeEditResTag(${JSON.stringify(String(t))})'>✕</button></span>`)
      .join('');
  }

  function formatJsonEditor(editorId, msgId) {
    try {
      const el = q(editorId);
      const parsed = parseJsonText(el.value);
      el.value = JSON.stringify(parsed, null, 2);
      if (msgId) setMsg(msgId, 'JSON formatted.');
      return true;
    } catch (e) {
      if (msgId) setMsg(msgId, `Invalid JSON: ${e.message}`, false);
      return false;
    }
  }

  function validateJsonEditor(editorId, msgId) {
    try {
      parseJsonText(q(editorId).value);
      if (msgId) setMsg(msgId, 'JSON is valid.');
      return true;
    } catch (e) {
      if (msgId) setMsg(msgId, `Invalid JSON: ${e.message}`, false);
      return false;
    }
  }

  function setSettingsMsg(text, ok = true) {
    const el = q('settingsMsg');
    if (!el) return;
    el.className = `settings-msg${ok ? '' : ' err'}`;
    el.textContent = text || '';
  }

  function setWriteModeActionMsg(text, ok = true) {
    const el = q('setWriteModeActionMsg');
    if (!el) return;
    el.className = `settings-action-msg${ok ? '' : ' err'}`;
    el.textContent = text || '';
  }

  function runEntityLabel(run) {
    if (!run || String(run.job_type || '') !== 'score_match') return '';
    const payload = run.payload || {};
    const jobId = Number(payload.job_id || 0);
    const resumeId = Number(payload.resume_id || 0);
    const job = (state.jobs || []).find((j) => Number(j.id) === jobId);
    const resume = (state.resumes || []).find((r) => Number(r.id) === resumeId);
    const jobName = String((job && job.filename) || (jobId ? `job:${jobId}` : '')).trim();
    const resumeName = String((resume && resume.filename) || (resumeId ? `resume:${resumeId}` : '')).trim();
    if (!jobName && !resumeName) return '';
    return `${jobName} x ${resumeName}`.trim();
  }

  function isPauseRequested(run) {
    if (!run || String(run.status || '') !== 'running') return false;
    const payload = run.payload || {};
    return !!(payload && payload.pause_requested) || String(run.current_step || '') === 'pause_requested';
  }

  function updateRunStatusBars() {
    const runs = state.runs || [];
    const active = runs
      .filter((r) => r.status === 'queued' || r.status === 'running' || r.status === 'paused')
      .sort((a, b) => {
        const rank = (s) => (s === 'running' ? 0 : s === 'paused' ? 1 : 2);
        const pa = rank(a.status);
        const pb = rank(b.status);
        if (pa !== pb) return pa - pb;
        return Number(b.id || 0) - Number(a.id || 0);
      });

    const selectedRunId = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
    const selected = runs.find((r) => Number(r.id) === selectedRunId) || active[0] || null;
    const jobPct = selected ? Math.max(0, Math.min(100, Number(selected.progress || 0))) : 0;
    const entity = selected ? runEntityLabel(selected) : '';
    const jobLabel = selected
      ? `Current Job • #${selected.id} • ${selected.status || 'unknown'}${entity ? ` • ${entity}` : ''}`
      : 'Current Job • idle';
    const jobStep = selected ? String(selected.current_step || '-') : 'No active run';

    if (q('jobProgressLabel')) q('jobProgressLabel').textContent = jobLabel;
    if (q('jobProgressMeta')) q('jobProgressMeta').textContent = `${jobPct}% • ${jobStep}`;
    if (q('jobProgressFill')) q('jobProgressFill').style.width = `${jobPct}%`;

    const ids = (state.analysisQueuedRunIds || []).map((x) => Number(x)).filter(Boolean);
    if (ids.length) {
      const rows = ids.map((id) => runs.find((r) => Number(r.id) === id)).filter(Boolean);
      const known = rows.length;
      const total = ids.length;
      const completed = rows.filter((r) => r.status === 'completed').length;
      const failed = rows.filter((r) => r.status === 'failed').length;
      const canceled = rows.filter((r) => r.status === 'canceled').length;
      const running = rows.filter((r) => r.status === 'running' && !isPauseRequested(r)).length;
      const paused = rows.filter((r) => r.status === 'paused' || isPauseRequested(r)).length;
      const queuedKnown = rows.filter((r) => r.status === 'queued').length;
      const queuedUnknown = Math.max(0, total - known);
      const queued = queuedKnown + queuedUnknown;
      const done = completed + failed + canceled;
      const pct = total ? Math.round((done / total) * 100) : 0;
      const failPart = failed ? `, ${failed} failed` : '';
      const canceledPart = canceled ? `, ${canceled} canceled` : '';
      const runPart = running ? `, ${running} running` : '';
      const pausedPart = paused ? `, ${paused} paused` : '';
      const queuePart = queued ? `, ${queued} queued` : '';

      if (q('batchProgressLabel')) q('batchProgressLabel').textContent = `Batch Progress • ${total} job(s)`;
      if (q('batchProgressMeta')) q('batchProgressMeta').textContent = `${completed}/${total} complete${failPart}${canceledPart}${runPart}${pausedPart}${queuePart}`;
      if (q('batchProgressFill')) q('batchProgressFill').style.width = `${pct}%`;
      return;
    }

    if (q('batchProgressLabel')) q('batchProgressLabel').textContent = 'Batch Progress';
    if (q('batchProgressMeta')) q('batchProgressMeta').textContent = 'No submitted batch';
    if (q('batchProgressFill')) q('batchProgressFill').style.width = '0%';
  }

  function updateRunHealthBanner() {
    const box = q('runHealthBox');
    const meta = q('runHealthMeta');
    const btn = q('resumeRunBtn');
    const pauseBtn = q('pauseRunBtn');
    const skipBtn = q('skipCurrentBtn');
    const cancelBtn = q('cancelRunBtn');
    const cancelBatchBtn = q('cancelBatchBtn');
    if (!box || !meta || !btn || !pauseBtn || !skipBtn || !cancelBtn || !cancelBatchBtn) return;
    const selectedRunId = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
    const run = (state.runs || []).find((r) => Number(r.id) === selectedRunId) || null;
    const rows = (state.runs || []).slice();
    const pausedLike = rows.filter((r) => String(r.status || '') === 'paused' || isPauseRequested(r));
    const runningLike = rows.filter((r) => String(r.status || '') === 'running' && !isPauseRequested(r));
    const queuedLike = rows.filter((r) => String(r.status || '') === 'queued');
    btn.style.display = 'none';
    pauseBtn.style.display = (pausedLike.length || runningLike.length || queuedLike.length) ? 'inline-flex' : 'none';
    skipBtn.style.display = runningLike.length ? 'inline-flex' : 'none';
    if (state.queuePauseActionInFlight) {
      pauseBtn.disabled = true;
      pauseBtn.textContent = pausedLike.length ? '⏳ Unpausing Queue...' : '⏳ Pausing Queue...';
    } else {
      pauseBtn.disabled = false;
      pauseBtn.textContent = pausedLike.length ? '▶️ Unpause Queue' : '⏸ Pause Queue';
    }
    cancelBtn.style.display = 'none';
    cancelBatchBtn.style.display = (runningLike.length || queuedLike.length || pausedLike.length) ? 'inline-flex' : 'none';
    box.classList.remove('stuck');
    if (!run) {
      meta.textContent = 'No active run selected.';
      return;
    }
    const status = String(run.status || 'unknown');
    const step = String(run.current_step || '-');
    const pct = Number(run.progress || 0);
    const stuck = !!run.is_stuck;
    const payload = run.payload || {};
    const pauseRequested = !!(payload && payload.pause_requested);
    const pauseReason = String((payload && payload.pause_reason) || 'Paused by user');
    const entity = runEntityLabel(run);
    const marker = run.last_log_at || run.started_at || run.created_at || '';
    let lagSec = 0;
    if (marker) {
      const ts = Date.parse(String(marker));
      if (!Number.isNaN(ts)) {
        lagSec = Math.max(0, Math.floor((Date.now() - ts) / 1000));
      }
    }
    if (stuck) {
      const sec = Number(run.stuck_seconds || 0);
      meta.textContent = `Run #${run.id}${entity ? ` (${entity})` : ''} appears stuck (${sec}s without progress). Last step: ${step}.`;
      box.classList.add('stuck');
      btn.style.display = 'inline-flex';
      cancelBtn.style.display = 'inline-flex';
      return;
    }
    if (status === 'paused') {
      meta.textContent = `Run #${run.id}${entity ? ` (${entity})` : ''} is paused at ${pct}% • step: ${step}`;
      cancelBtn.style.display = 'inline-flex';
      return;
    }
    if (status === 'running' && pauseRequested) {
      meta.textContent = `Run #${run.id}${entity ? ` (${entity})` : ''} pause requested (${pauseReason}) • step: ${step}`;
      cancelBtn.style.display = 'inline-flex';
      return;
    }
    if (status === 'queued' || status === 'running') {
      pauseBtn.style.display = 'inline-flex';
      cancelBtn.style.display = 'inline-flex';
    }
    if (status === 'running' && lagSec >= 45) {
      meta.textContent = `Run #${run.id}${entity ? ` (${entity})` : ''} is active at ${pct}% • waiting on model response for ~${lagSec}s • step: ${step}`;
      return;
    }
    meta.textContent = `Run #${run.id}${entity ? ` (${entity})` : ''} is ${status} at ${pct}% • step: ${step}`;
  }

  function updateAnalysisQueueMessage() {
    const ids = (state.analysisQueuedRunIds || []).map((x) => Number(x)).filter(Boolean);
    if (!ids.length) {
      if (!hasLiveQueueRuns()) stopAnalysisAutoPoll();
      updateRunStatusBars();
      return;
    }

    const rows = ids
      .map((id) => state.runs.find((r) => Number(r.id) === id))
      .filter(Boolean);
    if (!rows.length) {
      clearTrackedBatchRunIds();
      setMsg('msgMatch', '', true);
      if (!hasLiveQueueRuns()) stopAnalysisAutoPoll();
      updateRunStatusBars();
      return;
    }

    const completed = rows.filter((r) => r.status === 'completed').length;
    const running = rows.filter((r) => r.status === 'running').length;
    const queued = rows.filter((r) => r.status === 'queued').length;
    const paused = rows.filter((r) => r.status === 'paused' || isPauseRequested(r)).length;
    const failed = rows.filter((r) => r.status === 'failed').length;
    const canceled = rows.filter((r) => r.status === 'canceled').length;

    const idPreview = ids.length <= 6 ? ids.join(', ') : `${ids.slice(0, 6).join(', ')}, ...`;
    const total = ids.length;
    if (completed + canceled === total && failed === 0) {
      setMsg('msgMatch', '', true);
      clearTrackedBatchRunIds();
      if (!hasLiveQueueRuns()) stopAnalysisAutoPoll();
      updateRunStatusBars();
      return;
    }
    if (completed + failed + canceled >= total) {
      // Terminal state reached for tracked batch.
      clearTrackedBatchRunIds();
      if (!hasLiveQueueRuns()) stopAnalysisAutoPoll();
    }

    const text = `Tracking batch runs #${idPreview} (${total} total).`;
    setMsg('msgMatch', text, failed === 0);
    updateRunStatusBars();
  }

  function startAnalysisAutoPoll() {
    state.analysisAutoPollEnabled = true;
  }

  function stopAnalysisAutoPoll() {
    state.analysisAutoPollEnabled = false;
  }

  function getPinnedRunId() {
    const pinned = Number(state.logPinnedRunId || 0);
    if (!pinned) return 0;
    const exists = (state.runs || []).some((r) => Number(r.id) === pinned);
    if (!exists) {
      state.logPinnedRunId = null;
      return 0;
    }
    return pinned;
  }

  async function onActiveRunSelection() {
    const id = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
    state.logPinnedRunId = id || null;
    state.logAutoFollow = true;
    if (q('historyRunId') && id) q('historyRunId').value = '';
    await loadLogs(id || null);
  }

  async function onHistoryRunSelection() {
    const raw = String((q('historyRunId') && q('historyRunId').value) || '').trim();
    state.logPinnedRunId = raw || null;
    state.logAutoFollow = true;
    if (q('selectedRunId') && raw) q('selectedRunId').value = '';
    if (!raw) return;
    if (raw.startsWith('legacy:')) {
      await loadLegacyHistoryLog(Number(raw.split(':')[1] || 0));
      return;
    }
    await loadLogs(Number(raw) || null);
  }

  function switchTop(name) {
    ['results', 'analysis', 'manage'].forEach((t) => {
      q(`tab-${t}`).classList.toggle('active', t === name);
      q(`panel-${t}`).classList.toggle('active', t === name);
    });
  }

  function toggleSettingsMenu(event) {
    if (event) event.stopPropagation();
    q('settingsMenu').classList.toggle('open');
  }

  function closeSettingsMenu() {
    q('settingsMenu').classList.remove('open');
  }

  async function settingsAction(action) {
    closeSettingsMenu();
    if (action === 'refresh') {
      await refreshAll();
      await loadSettings();
      await refreshRunPanels();
      return;
    }
  }

  function updateReadOnlyInfo() {
    const writeMode = !!(state.settings && state.settings.write_mode);
    const top = q('topReadOnlyInfo');
    if (writeMode) {
      if (top) top.textContent = '✅ Write mode enabled: local changes can be pushed to shared DB.';
    } else {
      if (top) top.textContent = '🔒 Read-only mode: changes are local only and will NOT sync to the shared DB. Enable Write Mode to share results.';
    }
  }

  function renderSettingsControls() {
    const s = state.settings || {};
    q('setLmUrl').value = s.lm_base_url || '';
    q('setApiKey').value = s.lm_api_key || '';
    renderSettingsModelSelect(Array.isArray(state.settingsModels) ? state.settingsModels : [], s.lm_model || '');
    q('setOcrEnabled').checked = !!s.ocr_enabled;
    if (q('aiConcurrencyInput')) {
      const v = Number(s.ai_concurrency || 1);
      q('aiConcurrencyInput').value = String(Math.max(1, Number.isFinite(v) ? v : 1));
    }
    if (q('jobConcurrencyInput')) {
      const v = Number(s.job_concurrency || 1);
      q('jobConcurrencyInput').value = String(Math.max(1, Number.isFinite(v) ? v : 1));
    }
    q('setWriterName').value = q('setWriterName').value || s.writer_default_name || '';
    const users = Array.isArray(s.writer_users) ? s.writer_users.filter(Boolean) : [];
    const usersHint = q('setWriterUsersHint');
    if (usersHint) {
      usersHint.textContent = users.length ? `Allowed users: ${users.join(', ')}` : '';
    }
    if (users.length && !q('setWriterName').value) q('setWriterName').value = users[0];

    const lock = s.lock_info || null;
    let lockText = 'Write lock: none';
    if (lock && typeof lock === 'object' && !lock.error) {
      const owner = lock.owner || 'unknown';
      const created = lock.created_at || 'unknown';
      lockText = lock.expired ? `Write lock: ${owner} since ${created} (expired)` : `Write lock: ${owner} since ${created}`;
    } else if (lock && lock.error) {
      lockText = `Write lock: ${lock.error}`;
    }
    q('setWriteLockInfo').textContent = lockText;

    const statusEl = q('setWriteModeStatus');
    if (statusEl) {
      const lockOwner = lock && typeof lock === 'object' ? String(lock.owner || '').trim() : '';
      if (s.write_mode) {
        statusEl.className = 'settings-inline-status ok';
        statusEl.textContent = lockOwner
          ? `Write Mode Active. Lock owner: ${lockOwner}.`
          : 'Write Mode Active. You can push local changes.';
      } else if (s.write_mode_locked) {
        statusEl.className = 'settings-inline-status err';
        statusEl.textContent = 'Write Mode Locked by environment.';
      } else {
        statusEl.className = 'settings-inline-status warn';
        statusEl.textContent = 'Read-Only Mode. Enable Write Mode to allow push.';
      }
    }
    updateReadOnlyInfo();
  }

  async function loadSettings() {
    try {
      state.settings = await getJson('/v1/settings/state');
      renderSettingsControls();
      await loadSettingsModels(false);
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  function renderSettingsModelSelect(models, selected) {
    const sel = q('setLmModel');
    if (!sel) return;
    const uniq = Array.from(new Set((models || []).map((x) => String(x || '').trim()).filter(Boolean)));
    sel.innerHTML = '<option value="">Auto-select model</option>' + uniq.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join('');
    const wanted = String(selected || '').trim();
    if (wanted && !uniq.includes(wanted)) {
      sel.innerHTML += `<option value="${escapeHtml(wanted)}">${escapeHtml(wanted)} (current)</option>`;
    }
    if (wanted) sel.value = wanted;
  }

  async function loadSettingsModels(showMsg = true) {
    try {
      const r = await send('/v1/settings/models', 'POST', {
        lm_base_url: q('setLmUrl').value.trim(),
        lm_api_key: q('setApiKey').value.trim(),
      });
      if (!r.ok) throw new Error(r.message || 'Failed to fetch models');
      state.settingsModels = Array.isArray(r.models) ? r.models : [];
      renderSettingsModelSelect(state.settingsModels, (state.settings && state.settings.lm_model) || q('setLmModel').value);
      if (showMsg) setSettingsMsg(`Loaded ${state.settingsModels.length} model(s).`);
    } catch (e) {
      if (showMsg) setSettingsMsg(e.message, false);
    }
  }

  async function saveSettingsConfig() {
    try {
      await send('/v1/settings/runtime', 'PUT', {
        lm_base_url: q('setLmUrl').value.trim(),
        lm_api_key: q('setApiKey').value.trim(),
        lm_model: q('setLmModel').value.trim(),
        ocr_enabled: q('setOcrEnabled').checked,
        ai_concurrency: Math.max(1, Number(q('aiConcurrencyInput')?.value || 1)),
        job_concurrency: Math.max(1, Number(q('jobConcurrencyInput')?.value || 1)),
      });
      await loadSettings();
      setSettingsMsg('Configuration saved.');
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  async function testSettingsConnection() {
    try {
      const r = await send('/v1/settings/test-connection', 'POST', {
        lm_base_url: q('setLmUrl').value.trim(),
        lm_api_key: q('setApiKey').value.trim(),
      });
      setSettingsMsg(r.message || 'Connection test completed.', !!r.ok);
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  async function enableWriteMode() {
    try {
      const r = await send('/v1/settings/write-mode/enable', 'POST', {
        writer_name: q('setWriterName').value.trim(),
        writer_password: q('setWriterPassword').value,
      });
      await loadSettings();
      setWriteModeActionMsg(`✅ ${r.message || 'Write mode enabled.'}`, true);
      setSettingsMsg(r.message || 'Write mode enabled.');
    } catch (e) {
      setWriteModeActionMsg(`❌ ${e.message}`, false);
      setSettingsMsg(e.message, false);
    }
  }

  async function disableWriteMode() {
    try {
      const r = await send('/v1/settings/write-mode/disable', 'POST', {
        writer_name: q('setWriterName').value.trim(),
        writer_password: q('setWriterPassword').value,
      });
      await loadSettings();
      setWriteModeActionMsg(`✅ ${r.message || 'Write mode disabled.'}`, true);
      setSettingsMsg(r.message || 'Write mode disabled.');
    } catch (e) {
      setWriteModeActionMsg(`❌ ${e.message}`, false);
      setSettingsMsg(e.message, false);
    }
  }

  async function forceUnlockWriteMode() {
    try {
      const r = await send('/v1/settings/write-mode/force-unlock', 'POST', {
        writer_name: q('setWriterName').value.trim(),
        writer_password: q('setWriterPassword').value,
      });
      await loadSettings();
      setWriteModeActionMsg(`✅ ${r.message || 'Lock released.'}`, true);
      setSettingsMsg(r.message || 'Lock released.');
    } catch (e) {
      setWriteModeActionMsg(`❌ ${e.message}`, false);
      setSettingsMsg(e.message, false);
    }
  }

  async function pushToGithub() {
    try {
      const r = await send('/v1/settings/sync/push', 'POST', {});
      setSettingsMsg(r.message || 'Database pushed to GitHub.');
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  async function pullFromGithub() {
    try {
      const r = await send('/v1/settings/sync/pull', 'POST', {});
      await refreshAll();
      setSettingsMsg(r.message || 'Database pulled from GitHub.');
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  async function resetDatabase() {
    try {
      const ok = await openConfirmModal({
        title: 'Reset Database',
        message: 'Reset DB will delete jobs, resumes, matches, and runs. Continue?',
        confirmText: 'Reset DB',
      });
      if (!ok) return;
      const r = await send('/v1/settings/reset-db', 'POST', {});
      await refreshAll();
      await loadSettings();
      setSettingsMsg(r.message || 'Database reset complete.');
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  async function clearResultsOnly() {
    try {
      const ok = await openConfirmModal({
        title: 'Clear Results Only',
        message: 'This will delete matches and run history only. Jobs, resumes, tags, and extracted content will be kept. Continue?',
        confirmText: 'Clear Results',
      });
      if (!ok) return;
      const r = await send('/v1/settings/clear-results', 'POST', {});
      clearTrackedBatchRunIds();
      state.logPinnedRunId = null;
      await refreshAll();
      await loadSettings();
      setSettingsMsg(r.message || 'Cleared matches and run history.');
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  function switchManage(name) {
    const uploadMode = name === 'upload';
    if (q('sub-manage-upload')) q('sub-manage-upload').classList.toggle('active', uploadMode);
    if (q('sub-manage-data')) q('sub-manage-data').classList.toggle('active', !uploadMode);
    ['jd', 'res', 'tags', 'verify'].forEach((t) => {
      const panel = q(`panel-manage-${t}`);
      if (!panel) return;
      const visible = uploadMode ? (t === 'jd' || t === 'res') : (t === 'tags' || t === 'verify');
      panel.classList.toggle('active', visible);
      panel.style.display = visible ? '' : 'none';
    });
    if (!uploadMode) {
      const verifyPanel = q('panel-manage-verify');
      const tagsPanel = q('panel-manage-tags');
      const manageRoot = q('panel-manage');
      if (verifyPanel && tagsPanel && manageRoot && tagsPanel.previousElementSibling !== verifyPanel) {
        manageRoot.insertBefore(verifyPanel, tagsPanel);
      }
    }
    document.querySelectorAll('.manage-upload-section').forEach((el) => {
      el.style.display = uploadMode ? '' : 'none';
    });
    document.querySelectorAll('.manage-data-section').forEach((el) => {
      el.style.display = uploadMode ? 'none' : '';
    });
    if (!uploadMode) renderUnifiedDataBrowser();
  }

  function getUnifiedDataRows() {
    const mode = String((q('manageEntityType') && q('manageEntityType').value) || 'all');
    const tag = String((q('manageEntityTag') && q('manageEntityTag').value) || 'All');
    const search = String((q('manageEntitySearch') && q('manageEntitySearch').value) || '').trim().toLowerCase();
    const source = mode === 'all'
      ? [
          ...(state.jobs || []).map((row) => ({ ...row, _entityType: 'job' })),
          ...(state.resumes || []).map((row) => ({ ...row, _entityType: 'resume' })),
        ]
      : (mode === 'resume'
          ? (state.resumes || []).map((row) => ({ ...row, _entityType: 'resume' }))
          : (state.jobs || []).map((row) => ({ ...row, _entityType: 'job' })));
    return source.filter((row) => {
      const filename = String(row.filename || '');
      const tags = (row.tags || []).map((t) => String(t).trim());
      if (tag !== 'All' && !tags.includes(tag)) return false;
      if (search && !filename.toLowerCase().includes(search)) return false;
      return true;
    });
  }

  function renderUnifiedDataBrowser() {
    const select = q('manageEntitySelect');
    const table = q('manageEntityTable');
    const count = q('manageEntityCount');
    const mode = String((q('manageEntityType') && q('manageEntityType').value) || 'all');
    const tag = q('manageEntityTag');
    if (tag && !tag.options.length) {
      tag.innerHTML = '<option value="All">All Tags</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
      if (!tag.value) tag.value = 'All';
    }
    if (!select || !table || !count) return;
    const rows = getUnifiedDataRows();
    const prev = String(select.value || '');
    select.innerHTML = '<option value="">Select document</option>' + rows.map((r) => {
      const key = `${String(r._entityType || mode)}:${Number(r.id)}`;
      return `<option value="${escapeHtml(key)}">${escapeHtml(r.filename || '')}</option>`;
    }).join('');
    if (prev && rows.some((r) => `${String(r._entityType || mode)}:${Number(r.id)}` === prev)) select.value = prev;
    count.textContent = `${rows.length} item(s)`;
    table.innerHTML = '<table><thead><tr><th>Type</th><th>Filename</th><th>Tags</th><th>Upload Date</th></tr></thead><tbody>' +
      rows.map((r) => {
        const key = `${String(r._entityType || mode)}:${Number(r.id)}`;
        const typeLabel = String(r._entityType || mode) === 'resume' ? 'Resume' : 'JD';
        return `<tr style="cursor:pointer" onclick="openUnifiedDataRecord('${escapeHtml(key)}')"><td>${typeLabel}</td><td>${escapeHtml(r.filename || '')}</td><td>${escapeHtml((r.tags || []).join(', '))}</td><td>${escapeHtml(r.upload_date || '')}</td></tr>`;
      }).join('') +
      '</tbody></table>';
    const selectedKey = String(select.value || '');
    if (!selectedKey && rows.length) {
      const first = rows[0];
      select.value = `${String(first._entityType || mode)}:${Number(first.id)}`;
    }
    if (String(select.value || '').includes(':')) {
      openUnifiedDataRecord(String(select.value || ''), true);
    } else {
      if (q('unifiedEditTitle')) q('unifiedEditTitle').textContent = mode === 'job' ? 'JD Details' : 'Resume Details';
      if (q('unifiedEditingLabel')) q('unifiedEditingLabel').textContent = 'Editing: none selected';
      if (q('unifiedRaw')) q('unifiedRaw').textContent = '';
      if (q('unifiedTagsCsv')) q('unifiedTagsCsv').value = '';
      renderUnifiedEditTagChips();
      if (q('unifiedJsonHeading')) q('unifiedJsonHeading').textContent = mode === 'job' ? 'JSON Criteria' : 'JSON Profile';
      if (q('unifiedJsonEditor')) q('unifiedJsonEditor').value = '';
      state.selectedUnifiedType = null;
      state.selectedUnifiedId = null;
      state.verifyData = null;
      state.verifyItems = [];
      if (q('verifyContext')) q('verifyContext').textContent = 'Select a document from Document Browser to load verification details.';
      if (q('verifyRaw')) q('verifyRaw').textContent = '';
      if (q('verifyJson')) q('verifyJson').textContent = '';
      if (q('verifyEvidence')) q('verifyEvidence').textContent = 'Select an item to inspect evidence.';
      if (q('verifyClosest')) q('verifyClosest').textContent = 'No query yet.';
      renderVerifyEvidenceTargets();
      renderVerifyTable();
    }
  }

  async function openUnifiedDataRecord(id = null, preserve = false) {
    try {
      const selectedRaw = String(id || (q('manageEntitySelect') && q('manageEntitySelect').value) || '').trim();
      const modeFromFilter = String((q('manageEntityType') && q('manageEntityType').value) || 'all');
      let mode = modeFromFilter === 'resume' ? 'resume' : 'job';
      let targetId = 0;
      if (selectedRaw.includes(':')) {
        const parts = selectedRaw.split(':');
        const parsedMode = String(parts[0] || '').trim();
        const parsedId = Number(parts[1] || 0);
        if (parsedMode === 'job' || parsedMode === 'resume') mode = parsedMode;
        targetId = parsedId;
      } else {
        targetId = Number(selectedRaw || 0);
      }
      if (!targetId) return;
      const selectKey = `${mode}:${targetId}`;
      if (!preserve && q('manageEntitySelect')) q('manageEntitySelect').value = selectKey;
      const rec = mode === 'job'
        ? await getJson(`/v1/jobs/${targetId}`)
        : await getJson(`/v1/resumes/${targetId}`);
      state.selectedUnifiedType = mode;
      state.selectedUnifiedId = Number(targetId);
      if (q('unifiedEditTitle')) q('unifiedEditTitle').textContent = mode === 'job' ? 'JD Details' : 'Resume Details';
      if (q('unifiedEditingLabel')) q('unifiedEditingLabel').textContent = `Editing: ${rec.filename || ''}`;
      if (q('unifiedRaw')) q('unifiedRaw').textContent = rec.content || '';
      if (q('unifiedTagsCsv')) q('unifiedTagsCsv').value = (rec.tags || []).join(', ');
      renderUnifiedEditTagChips();
      if (q('unifiedJsonHeading')) q('unifiedJsonHeading').textContent = mode === 'job' ? 'JSON Criteria' : 'JSON Profile';
      if (q('unifiedJsonEditor')) {
        const payload = mode === 'job' ? rec.criteria : rec.profile;
        q('unifiedJsonEditor').value = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
        formatJsonEditor('unifiedJsonEditor');
      }
      if (q('verifyMode')) q('verifyMode').value = mode;
      if (q('verifyTagFilter')) q('verifyTagFilter').value = 'All';
      if (q('verifyContext')) q('verifyContext').textContent = `Verifying selected ${mode === 'job' ? 'JD' : 'Resume'}: ${rec.filename || ''}`;
      state.verifyData = rec;
      state.verifyItems = extractVerifyItems(mode, rec);
      if (q('verifyRaw')) q('verifyRaw').textContent = rec.content || '';
      const parsed = mode === 'job' ? rec.criteria : rec.profile;
      if (q('verifyJson')) q('verifyJson').textContent = typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
      if (q('verifyEvidence')) q('verifyEvidence').textContent = 'Select an item to inspect evidence.';
      if (q('verifyClosest')) q('verifyClosest').textContent = 'No query yet.';
      renderVerifyEvidenceTargets();
      renderVerifyTable();
      const editor = q('unifiedDataEditor');
      if (editor && !preserve) editor.scrollIntoView({ block: 'start', behavior: 'smooth' });
    } catch (e) {
      debugLog(`Open data record failed: ${e.message}`, 'warn');
    }
  }

  async function saveUnifiedRecord() {
    try {
      const mode = String(state.selectedUnifiedType || '');
      const id = Number(state.selectedUnifiedId || 0);
      if (!mode || !id) throw new Error('Select a document first.');
      if (!validateJsonEditor('unifiedJsonEditor', 'msgUnifiedEdit')) return;
      const parsed = JSON.stringify(parseJsonText(q('unifiedJsonEditor').value));
      const tags = tagsFrom(q('unifiedTagsCsv').value);
      if (mode === 'job') {
        await send(`/v1/jobs/${id}`, 'PUT', { criteria: parsed, tags });
      } else {
        await send(`/v1/resumes/${id}`, 'PUT', { profile: parsed, tags });
      }
      setMsg('msgUnifiedEdit', 'Saved.');
      await refreshAll();
      if (q('manageEntityType')) q('manageEntityType').value = mode;
      if (q('manageEntitySelect')) q('manageEntitySelect').value = String(id);
      await openUnifiedDataRecord(id, true);
    } catch (e) {
      setMsg('msgUnifiedEdit', e.message, false);
    }
  }

  async function reprocessUnifiedRecord() {
    try {
      const mode = String(state.selectedUnifiedType || '');
      const id = Number(state.selectedUnifiedId || 0);
      if (!mode || !id) throw new Error('Select a document first.');
      const rec = mode === 'job'
        ? await getJson(`/v1/jobs/${id}`)
        : await getJson(`/v1/resumes/${id}`);
      const run = await send('/v1/runs', 'POST', {
        job_type: mode === 'job' ? 'reprocess_job' : 'reprocess_resume',
        payload: mode === 'job' ? { job_id: id } : { resume_id: id },
      });
      const runId = Number(run && run.id);
      if (runId) {
        state.reprocessRunId = runId;
        if (q('selectedRunId')) q('selectedRunId').value = String(runId);
        state.logPinnedRunId = null;
        setTrackedBatchRunIds([runId]);
        startAnalysisAutoPoll();
        await refreshRunPanels();
        await loadLogs(runId);
      }
      setMsg('msgUnifiedEdit', `Queued reprocess run #${runId} for ${rec.filename || 'selected document'}.`);
      await refreshAll();
      await openUnifiedDataRecord(id, true);
    } catch (e) {
      setMsg('msgUnifiedEdit', e.message, false);
    }
  }

  async function deleteUnifiedRecord() {
    try {
      const mode = String(state.selectedUnifiedType || '');
      const id = Number(state.selectedUnifiedId || 0);
      if (!mode || !id) throw new Error('Select a document first.');
      const ok = await openConfirmModal({
        title: mode === 'job' ? 'Delete JD' : 'Delete Resume',
        message: `Delete selected ${mode === 'job' ? 'JD' : 'Resume'}? This cannot be undone.`,
        confirmText: 'Delete',
      });
      if (!ok) return;
      const url = mode === 'job' ? `/v1/jobs/${id}` : `/v1/resumes/${id}`;
      const r = await fetch(url, { method: 'DELETE' });
      if (!r.ok) throw new Error('Delete failed');
      setMsg('msgUnifiedEdit', 'Deleted.');
      state.selectedUnifiedId = null;
      await refreshAll();
      renderUnifiedDataBrowser();
    } catch (e) {
      setMsg('msgUnifiedEdit', e.message, false);
    }
  }

  function switchResults(name) {
    ['simple', 'run'].forEach((t) => {
      const panel = q(`panel-results-${t}`);
      if (!panel) return;
      panel.classList.toggle('active', t === name);
      panel.style.display = t === name ? '' : 'none';
    });
  }

  function toggleResultsMode() {
    const simple = !!(q('resultsSimpleMode') && q('resultsSimpleMode').checked);
    switchResults(simple ? 'simple' : 'run');
  }

  function decisionBadge(decision) {
    const d = String(decision || '').toLowerCase();
    if (d.includes('move')) return '<span class="badge move">Move Forward</span>';
    if (d.includes('review')) return '<span class="badge review">Review</span>';
    if (d.includes('reject')) return '<span class="badge reject">Reject</span>';
    return `<span class="badge">${decision || ''}</span>`;
  }

  function fillSelect(id, rows, labelFn, includeBlank = true) {
    const el = q(id);
    if (!el) return;
    const prev = el.value;
    let html = includeBlank ? '<option value="">Select</option>' : '';
    html += rows.map((r) => `<option value="${r.id}">${labelFn(r)}</option>`).join('');
    el.innerHTML = html;
    if (prev && Array.from(el.options).some((o) => o.value === prev)) el.value = prev;
  }

  function renderJobs() {
    if (q('jdCount')) q('jdCount').textContent = `Use Document Browser above to select a JD. Total Job Descriptions: ${state.jobs.length}`;
    if (q('jobsTable')) {
      q('jobsTable').innerHTML = `<table><thead><tr><th>Filename</th><th>Tags</th><th>Upload Date</th></tr></thead><tbody>` +
        state.jobs.map((j) => `<tr style="cursor:pointer" onclick="selectJD(${j.id})"><td>${j.filename}</td><td>${(j.tags || []).join(', ')}</td><td>${j.upload_date || ''}</td></tr>`).join('') +
        `</tbody></table>`;
    }
    renderReparseJDOptions();
    fillSelect('simpleJobSelect', state.jobs, (x) => x.filename, false);
  }

  function renderResumes() {
    const selectedTag = String(q('resTagFilter').value || 'All');
    let rows = state.resumes;
    if (selectedTag !== 'All') {
      rows = rows.filter((r) => {
        const tags = (r.tags || []).map((t) => String(t).trim());
        return tags.includes(selectedTag);
      });
    }
    if (q('resCount')) q('resCount').textContent = `Use Document Browser above to select a Resume. Total Resumes: ${state.resumes.length} | Filtered: ${rows.length}`;
    if (q('resumesTable')) {
      q('resumesTable').innerHTML = `<table><thead><tr><th>Filename</th><th>Tags</th><th>Upload Date</th></tr></thead><tbody>` +
        rows.map((r) => `<tr style="cursor:pointer" onclick="selectResume(${r.id})"><td>${r.filename}</td><td>${(r.tags || []).join(', ')}</td><td>${r.upload_date || ''}</td></tr>`).join('') +
        `</tbody></table>`;
    }
    renderReparseResumeOptions();
  }

  function renderReparseJDOptions(filtered = null) {
    const sel = q('reparseJdSelect');
    if (!sel) return;
    const rows = filtered || state.jobs;
    const selected = new Set(Array.from(sel.selectedOptions || []).map((o) => String(o.value)));
    sel.innerHTML = rows.map((x) => `<option value="${x.id}">${x.filename}</option>`).join('');
    Array.from(sel.options).forEach((o) => {
      if (selected.has(o.value)) o.selected = true;
    });
    toggleReparseJDSelection();
  }

  function renderReparseResumeOptions(filtered = null) {
    const sel = q('reparseResSelect');
    if (!sel) return;
    const rows = filtered || state.resumes;
    const selected = new Set(Array.from(sel.selectedOptions || []).map((o) => String(o.value)));
    sel.innerHTML = rows.map((x) => `<option value="${x.id}">${x.filename}</option>`).join('');
    Array.from(sel.options).forEach((o) => {
      if (selected.has(o.value)) o.selected = true;
    });
    toggleReparseResSelection();
  }

  function toggleReparseJDSelection() {
    const scope = q('reparseJdScope').value;
    q('reparseJdSelect').disabled = scope !== 'selected';
    q('reparseJdSearch').disabled = scope !== 'selected';
  }

  function toggleReparseResSelection() {
    const scope = q('reparseResScope').value;
    q('reparseResSelect').disabled = scope !== 'selected';
    q('reparseResSearch').disabled = scope !== 'selected';
  }

  function filterReparseJDs() {
    const scope = q('reparseJdScope').value;
    if (scope !== 'selected') return;
    const term = String(q('reparseJdSearch').value || '').toLowerCase().trim();
    const filtered = !term ? state.jobs : state.jobs.filter((x) => String(x.filename || '').toLowerCase().includes(term));
    renderReparseJDOptions(filtered);
  }

  function filterReparseResumes() {
    const scope = q('reparseResScope').value;
    if (scope !== 'selected') return;
    const term = String(q('reparseResSearch').value || '').toLowerCase().trim();
    const filtered = !term ? state.resumes : state.resumes.filter((x) => String(x.filename || '').toLowerCase().includes(term));
    renderReparseResumeOptions(filtered);
  }

  function renderAnalysisSelectors() {
    const jobSel = q('matchJobSelect');
    const resumeSel = q('matchResumeSelect');
    const tagSel = q('analysisTagFilter');
    if (!jobSel || !resumeSel || !tagSel) return;

    const prevJob = jobSel.value;
    const prevResume = resumeSel.value;
    const prevTag = tagSel.value;

    jobSel.innerHTML = '<option value="__all__">All JDs</option>' + state.jobs.map((j) => `<option value="${j.id}">${j.filename}</option>`).join('');
    tagSel.innerHTML = '<option value="All">All</option>' + state.tags.map((t) => `<option value="${t}">${t}</option>`).join('');

    if (prevJob && Array.from(jobSel.options).some((o) => o.value === prevJob)) jobSel.value = prevJob;
    if (!jobSel.value) jobSel.value = '__all__';
    if (prevTag && Array.from(tagSel.options).some((o) => o.value === prevTag)) tagSel.value = prevTag;
    if (!tagSel.value) tagSel.value = 'All';

    applyAnalysisTagFilter(prevResume);
    const selectedJob = jobSel.value;
    const preview = getAnalysisSelectionPreview();
    let defaultName = `Run ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    if (selectedJob && selectedJob !== '__all__') {
      const job = state.jobs.find((j) => String(j.id) === String(selectedJob));
      if (job && job.filename) {
        defaultName = `Run: ${String(job.filename).replace(/\\.[^/.]+$/, '')}`;
      }
    } else {
      const jobCount = Math.max(1, Number(preview.effectiveJobs || 0));
      defaultName = `Batch Run: ${jobCount} Jobs`;
    }
    const runNameInput = q('runName');
    const currentValue = (runNameInput.value || '').trim();
    if (!currentValue || currentValue === state.lastAutoRunName) {
      runNameInput.value = defaultName;
    }
    state.lastAutoRunName = defaultName;
    onAnalysisSelectionChange();
  }

  function applyAnalysisTagFilter(preferredResume = null) {
    const resumeSel = q('matchResumeSelect');
    const tag = q('analysisTagFilter') ? q('analysisTagFilter').value : 'All';
    if (!resumeSel) return;
    let rows = state.resumes;
    if (tag && tag !== 'All') {
      rows = rows.filter((r) => (r.tags || []).map((x) => String(x).trim()).includes(tag));
    }
    const current = preferredResume || resumeSel.value;
    resumeSel.innerHTML = '<option value="__all__">All Resumes</option>' + rows.map((r) => `<option value="${r.id}">${r.filename}</option>`).join('');
    if (current && Array.from(resumeSel.options).some((o) => o.value === current)) resumeSel.value = current;
    if (!resumeSel.value) resumeSel.value = '__all__';
    onAnalysisSelectionChange();
  }

  function getAnalysisSelectionPreview() {
    const jdSel = q('matchJobSelect');
    const rsSel = q('matchResumeSelect');
    const autoTag = !!(q('analysisAutoTagMatch') && q('analysisAutoTagMatch').checked);
    const jobRows = (jdSel && jdSel.value && jdSel.value !== '__all__')
      ? state.jobs.filter((j) => String(j.id) === String(jdSel.value))
      : state.jobs.slice();

    let resumeIds = [];
    if (rsSel && rsSel.value === '__all__') {
      resumeIds = Array.from(rsSel.options || [])
        .map((o) => Number(o.value))
        .filter((v) => v && !Number.isNaN(v));
    } else if (rsSel && rsSel.value) {
      resumeIds = [Number(rsSel.value)].filter((v) => v && !Number.isNaN(v));
    }

    let effectiveJobs = 0;
    let effectivePairs = 0;
    for (const job of jobRows) {
      let perJobResumeIds = resumeIds.slice();
      const jdTags = (job && job.tags) ? job.tags.map((t) => String(t).trim()).filter(Boolean) : [];
      if (autoTag && jdTags.length) {
        perJobResumeIds = perJobResumeIds.filter((rid) => {
          const r = state.resumes.find((x) => Number(x.id) === Number(rid));
          const rTags = (r && r.tags) ? r.tags.map((t) => String(t).trim()) : [];
          return jdTags.some((t) => rTags.includes(t));
        });
      }
      if (perJobResumeIds.length) {
        effectiveJobs += 1;
        effectivePairs += perJobResumeIds.length;
      }
    }
    return {
      totalJobs: state.jobs.length,
      selectedJobsRaw: (jdSel && jdSel.value === '__all__') ? state.jobs.length : (jdSel && jdSel.value ? 1 : 0),
      selectedResumesRaw: resumeIds.length,
      effectiveJobs,
      effectivePairs,
    };
  }

  function buildLegacyRunNameForJob(baseRunName, job) {
    const jdName = (job && job.filename) ? String(job.filename).replace(/\\.[^/.]+$/, '') : '';
    const trimmedBase = String(baseRunName || '').trim();
    if (!trimmedBase) return jdName ? `Auto: ${jdName}` : 'Auto: Job';
    if (!jdName) return trimmedBase;
    if (trimmedBase.toLowerCase().includes(jdName.toLowerCase())) return trimmedBase;
    if (trimmedBase.toLowerCase().startsWith('batch run:')) return `Run: ${jdName}`;
    return `${trimmedBase} • ${jdName}`;
  }

  function onAnalysisSelectionChange() {
    const jdSel = q('matchJobSelect');
    const rsSel = q('matchResumeSelect');
    const preview = getAnalysisSelectionPreview();
    if (jdSel) {
      const selectedJob = jdSel.value;
      let defaultName = `Run ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      if (selectedJob && selectedJob !== '__all__') {
        const job = state.jobs.find((j) => String(j.id) === String(selectedJob));
        if (job && job.filename) defaultName = `Run: ${String(job.filename).replace(/\\.[^/.]+$/, '')}`;
      } else {
        const jobCount = Math.max(1, Number(preview.effectiveJobs || 0));
        defaultName = `Batch Run: ${jobCount} Jobs`;
      }
      const runNameInput = q('runName');
      const currentValue = (runNameInput.value || '').trim();
      if (!currentValue || currentValue === state.lastAutoRunName) runNameInput.value = defaultName;
      state.lastAutoRunName = defaultName;
    }
    const jdCount = Number(preview.effectiveJobs || 0);
    const resOptions = rsSel ? Array.from(rsSel.options).filter((o) => o.value !== '__all__').length : 0;
    const rsCount = rsSel && rsSel.value === '__all__' ? Number(preview.selectedResumesRaw || 0) : (rsSel && rsSel.value ? 1 : 0);
    q('selectedCountJd').textContent = `Selected JDs: ${jdCount} / ${state.jobs.length}`;
    q('selectedCountRes').textContent = `Selected Resumes: ${rsCount} / ${resOptions}`;
  }

  function renderTags() {
    if (!q('tagCount')) return;
    q('tagCount').textContent = `Total Tags: ${state.tags.length}`;
    const renameSelect = q('renameTagOld');
    const deleteSelect = q('deleteTagSel');
    const prevRenameOld = renameSelect ? renameSelect.value : '';
    const prevDelete = deleteSelect ? deleteSelect.value : '';
    const opts = '<option value="">Select</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    if (renameSelect) renameSelect.innerHTML = opts;
    if (deleteSelect) deleteSelect.innerHTML = opts;
    if (renameSelect && prevRenameOld && Array.from(renameSelect.options).some((o) => o.value === prevRenameOld)) {
      renameSelect.value = prevRenameOld;
    }
    if (deleteSelect && prevDelete && Array.from(deleteSelect.options).some((o) => o.value === prevDelete)) {
      deleteSelect.value = prevDelete;
    }
    const prevJdAssign = q('jdTagAssign').value;
    q('jdTagAssign').innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    if (prevJdAssign && Array.from(q('jdTagAssign').options).some((o) => o.value === prevJdAssign)) {
      q('jdTagAssign').value = prevJdAssign;
    }

    const prevAutoAssign = q('autoTagAssign') ? q('autoTagAssign').value : '';
    if (q('autoTagAssign')) {
      q('autoTagAssign').innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
      if (prevAutoAssign && Array.from(q('autoTagAssign').options).some((o) => o.value === prevAutoAssign)) {
        q('autoTagAssign').value = prevAutoAssign;
      }
    }

    const prevJdEdit = q('editJdTagSelect').value;
    q('editJdTagSelect').innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    if (prevJdEdit && Array.from(q('editJdTagSelect').options).some((o) => o.value === prevJdEdit)) {
      q('editJdTagSelect').value = prevJdEdit;
    }

    const prevResAssign = q('resTagAssign').value;
    q('resTagAssign').innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    if (prevResAssign && Array.from(q('resTagAssign').options).some((o) => o.value === prevResAssign)) {
      q('resTagAssign').value = prevResAssign;
    }
    renderJdUploadTagChips();
    renderAutoUploadTagChips();
    renderResUploadTagChips();

    const prevResEdit = q('editResTagSelect').value;
    q('editResTagSelect').innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    if (prevResEdit && Array.from(q('editResTagSelect').options).some((o) => o.value === prevResEdit)) {
      q('editResTagSelect').value = prevResEdit;
    }
    const unifiedTagSel = q('unifiedTagSelect');
    if (unifiedTagSel) {
      const prevUnifiedTag = unifiedTagSel.value || '';
      unifiedTagSel.innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
      if (prevUnifiedTag && Array.from(unifiedTagSel.options).some((o) => o.value === prevUnifiedTag)) {
        unifiedTagSel.value = prevUnifiedTag;
      }
    }
    renderUnifiedEditTagChips();

    q('verifyTagFilter').innerHTML = '<option value="All">All Tags</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    const manageTag = q('manageEntityTag');
    if (manageTag) {
      const selectedManageTag = manageTag.value || 'All';
      manageTag.innerHTML = '<option value="All">All Tags</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
      if (Array.from(manageTag.options).some((o) => o.value === selectedManageTag)) manageTag.value = selectedManageTag;
    }
    const resFilter = q('resTagFilter');
    if (resFilter) {
      const selected = resFilter.value || 'All';
      resFilter.innerHTML = '<option value="All">All Tags</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
      if (Array.from(resFilter.options).some((o) => o.value === selected)) resFilter.value = selected;
    }
    renderTagCatalog();
    prefillRenameTag();
    updateDeleteTagImpact();
  }

  function getTagUsage(tag) {
    const normalized = String(tag || '').trim();
    if (!normalized) return { jd: 0, resume: 0, total: 0 };
    const jdCount = state.jobs.filter((j) => (j.tags || []).map((t) => String(t).trim()).includes(normalized)).length;
    const resumeCount = state.resumes.filter((r) => (r.tags || []).map((t) => String(t).trim()).includes(normalized)).length;
    return { jd: jdCount, resume: resumeCount, total: jdCount + resumeCount };
  }

  function renderTagCatalog() {
    const wrap = q('tagCatalog');
    if (!wrap) return;
    const search = String((q('tagSearch') && q('tagSearch').value) || '').trim().toLowerCase();
    const rows = state.tags.filter((t) => !search || String(t).toLowerCase().includes(search));
    if (!rows.length) {
      wrap.innerHTML = '<div class="caption" style="padding:10px;">No tags found.</div>';
      return;
    }
    wrap.innerHTML = rows.map((tag) => {
      const usage = getTagUsage(tag);
      const encodedTag = encodeURIComponent(String(tag));
      return `<button class="tag-catalog-item" data-tag="${encodedTag}" onclick="selectTagForActions(decodeURIComponent(this.dataset.tag))">
        <div>
          <div class="tag-catalog-name">${escapeHtml(tag)}</div>
          <div class="tag-catalog-meta">Used in ${usage.jd} JD(s), ${usage.resume} resume(s)</div>
        </div>
        <span class="tag-catalog-total">${usage.total}</span>
      </button>`;
    }).join('');
  }

  function selectTagForActions(tag) {
    if (q('renameTagOld')) q('renameTagOld').value = tag;
    if (q('deleteTagSel')) q('deleteTagSel').value = tag;
    prefillRenameTag();
    updateDeleteTagImpact();
  }

  function prefillRenameTag() {
    const old = q('renameTagOld') ? q('renameTagOld').value : '';
    const impact = q('renameTagImpact');
    if (!impact) return;
    if (!old) {
      impact.textContent = 'Select a tag to rename.';
      return;
    }
    const usage = getTagUsage(old);
    impact.textContent = `Current tag "${old}" appears in ${usage.jd} JD(s) and ${usage.resume} resume(s).`;
  }

  function updateDeleteTagImpact() {
    const name = q('deleteTagSel') ? q('deleteTagSel').value : '';
    const impact = q('deleteTagImpact');
    if (!impact) return;
    if (!name) {
      impact.textContent = 'Select a tag to see impact.';
      return;
    }
    const usage = getTagUsage(name);
    impact.textContent = `Deleting "${name}" removes it from ${usage.jd} JD(s) and ${usage.resume} resume(s).`;
  }

  function renderRuns() {
    const runs = state.runs || [];
    const active = runs
      .filter((r) => r.status === 'queued' || r.status === 'running' || r.status === 'paused')
      .sort((a, b) => {
        const rank = (s) => (s === 'running' ? 0 : s === 'paused' ? 1 : 2);
        const pa = rank(a.status);
        const pb = rank(b.status);
        if (pa !== pb) return pa - pb;
        const ida = Number(a.id || 0);
        const idb = Number(b.id || 0);
        if (String(a.status || '') === 'queued' && String(b.status || '') === 'queued') {
          return ida - idb; // front of queue first
        }
        return idb - ida;
      });
    const history = runs.filter((r) => r.status === 'completed' || r.status === 'failed' || r.status === 'canceled');
    const legacyHistory = (state.legacyRuns || []).map((r) => ({
      id: `legacy:${r.id}`,
      label: `legacy #${r.id} | ${r.name || 'Run'} | threshold ${r.threshold || 50}% | ${r.created_at || ''}`,
    }));

    const activeSel = q('selectedRunId');
    const historySel = q('historyRunId');
    if (!activeSel || !historySel) return;

    const prevHistory = historySel.value;

    const fmt = (r) => {
      const stuckTag = r.is_stuck ? ' | STUCK' : '';
      const entity = runEntityLabel(r);
      const statusLabel = isPauseRequested(r) ? 'pause_requested' : String(r.status || '');
      return `#${r.id} | ${r.job_type}${entity ? ` | ${entity}` : ''} | ${statusLabel}${stuckTag} | ${r.progress || 0}% | ${r.current_step || '-'}`;
    };

    if (active.length) {
      activeSel.innerHTML = active.map((r) => `<option value="${r.id}">${fmt(r)}</option>`).join('');
      if (state.logPinnedRunId && active.some((r) => Number(r.id) === Number(state.logPinnedRunId))) {
        activeSel.value = String(state.logPinnedRunId);
      } else {
        // Default to front active run (running > paused > queued), not stuck-first.
        activeSel.value = String(active[0].id);
      }
    } else {
      activeSel.innerHTML = '<option value="">No active runs</option>';
    }

    if (history.length || legacyHistory.length) {
      const queuedHistory = history.map((r) => `<option value="${r.id}">${fmt(r)}</option>`).join('');
      const legacyOpts = legacyHistory.map((r) => `<option value="${r.id}">${r.label}</option>`).join('');
      historySel.innerHTML = '<option value="">Select completed/failed/canceled run</option>' +
        (queuedHistory ? `<optgroup label="Background Queue Runs">${queuedHistory}</optgroup>` : '') +
        (legacyOpts ? `<optgroup label="Legacy Runs">${legacyOpts}</optgroup>` : '');

      const pinnedRaw = String(state.logPinnedRunId || '');
      const pinnedMatchesQueued = pinnedRaw && history.some((r) => String(r.id) === pinnedRaw);
      const pinnedMatchesLegacy = pinnedRaw && legacyHistory.some((r) => String(r.id) === pinnedRaw);
      if (pinnedMatchesQueued || pinnedMatchesLegacy) {
        historySel.value = pinnedRaw;
      } else if (prevHistory && Array.from(historySel.options).some((o) => o.value === prevHistory)) {
        historySel.value = prevHistory;
      } else {
        historySel.value = '';
      }
    } else {
      historySel.innerHTML = '<option value="">No completed/failed/canceled runs</option>';
    }

    const running = runs.filter((r) => r.status === 'running' && !isPauseRequested(r)).length;
    const queued = runs.filter((r) => r.status === 'queued').length;
    const paused = runs.filter((r) => r.status === 'paused' || isPauseRequested(r)).length;
    const completed = runs.filter((r) => r.status === 'completed').length;
    const failed = runs.filter((r) => r.status === 'failed').length;
    const canceled = runs.filter((r) => r.status === 'canceled').length;
    const stuckRuns = runs.filter((r) => r.status === 'running' && r.is_stuck);
    const stuck = stuckRuns.length;
    const activeTotal = running + queued + paused;
    if (activeTotal > 0) {
      const stuckPart = stuck ? ` | Stuck: ${stuck}` : '';
      q('runCounts').textContent = `Active jobs: ${activeTotal} (running ${running}, queued ${queued}, paused ${paused})${stuckPart}`;
    } else if (completed || failed || canceled) {
      q('runCounts').textContent = `No active queue jobs. Recent terminal: completed ${completed}, failed ${failed}, canceled ${canceled}.`;
    } else {
      q('runCounts').textContent = 'No active queue jobs.';
    }
    const stuckAlert = q('runStuckAlert');
    if (stuckAlert) {
      if (stuck > 0) {
        const ids = stuckRuns.map((r) => `#${r.id}`).join(', ');
        stuckAlert.style.display = 'block';
        stuckAlert.textContent = `Stuck jobs detected: ${ids}. Select one and use "Resume Stuck Run".`;
      } else {
        stuckAlert.style.display = 'none';
        stuckAlert.textContent = '';
      }
    }
    updateRunStatusBars();
    updateRunHealthBanner();
    updateStartAnalysisButtonState();
    updateAutoUploadStatus();
  }

  function updateStartAnalysisButtonState() {
    const btn = q('startAnalysisBtn');
    if (!btn) return;
    if (state.analysisSubmitting) {
      btn.disabled = true;
      btn.textContent = '⏳ SUBMITTING...';
      return;
    }
    const runs = state.runs || [];
    const running = runs.filter((r) => r.status === 'running' && !isPauseRequested(r)).length;
    const queued = runs.filter((r) => r.status === 'queued').length;
    const paused = runs.filter((r) => r.status === 'paused' || isPauseRequested(r)).length;
    if (running > 0) {
      btn.disabled = false;
      btn.textContent = `⏳ RUNNING (${running})`;
      return;
    }
    if (queued > 0) {
      btn.disabled = false;
      btn.textContent = `⏳ QUEUED (${queued})`;
      return;
    }
    if (paused > 0) {
      btn.disabled = false;
      btn.textContent = `⏸ PAUSED (${paused})`;
      return;
    }
    btn.disabled = false;
    btn.textContent = '🚀 START ANALYSIS';
  }

  function updateAutoUploadStatus() {
    const btn = q('autoUploadBtn');
    const live = q('autoUploadLive');
    const table = q('autoUploadResultsTable');
    if (!btn || !live) return;
    if (state.autoUploadSubmitting) {
      btn.disabled = true;
      btn.textContent = 'Submitting...';
      live.textContent = 'Submitting auto-detect upload runs...';
      if (table) {
        table.innerHTML = '<table><thead><tr><th>Run ID</th><th>Filename</th><th>Detected As</th><th>Status</th><th>Progress</th><th>Notes</th></tr></thead><tbody><tr><td colspan="6">Submitting runs...</td></tr></tbody></table>';
      }
      return;
    }
    const tracked = Array.from(new Set((state.autoUploadRunIds || []).map((x) => Number(x)).filter(Boolean)));
    if (!tracked.length) {
      btn.disabled = false;
      btn.textContent = 'Process Documents (Auto-detect)';
      live.textContent = 'No active auto-detect upload runs.';
      if (table) {
        table.innerHTML = '<table><thead><tr><th>Run ID</th><th>Filename</th><th>Detected As</th><th>Status</th><th>Progress</th><th>Notes</th></tr></thead><tbody><tr><td colspan="6">No upload runs in current batch.</td></tr></tbody></table>';
      }
      return;
    }
    const runsById = new Map((state.runs || []).map((r) => [Number(r.id), r]));
    const rows = tracked.map((id) => runsById.get(id)).filter(Boolean);
    if (!rows.length) {
      btn.disabled = false;
      btn.textContent = 'Process Documents (Auto-detect)';
      live.textContent = 'No active auto-detect upload runs.';
      if (table) {
        table.innerHTML = '<table><thead><tr><th>Run ID</th><th>Filename</th><th>Detected As</th><th>Status</th><th>Progress</th><th>Notes</th></tr></thead><tbody><tr><td colspan="6">Run data not available in current window.</td></tr></tbody></table>';
      }
      return;
    }
    if (table) {
      const byId = rows.slice().sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
      table.innerHTML = '<table><thead><tr><th>Run ID</th><th>Filename</th><th>Detected As</th><th>Status</th><th>Progress</th><th>Notes</th></tr></thead><tbody>' +
        byId.map((r) => {
          const payload = r && r.payload ? r.payload : {};
          const result = r && r.result ? r.result : {};
          const fname = String((payload && payload.filename) || (result && result.filename) || '');
          const dtype = String((result && result.document_type) || '').trim();
          const detected = dtype ? (dtype === 'job' ? 'JD' : 'Resume') : 'Pending';
          const status = String(r.status || '-');
          const progress = `${Number(r.progress || 0)}% • ${String(r.current_step || '-')}`;
          let notes = '';
          if (result && result.skipped) notes = 'Skipped existing (force reparse off)';
          else if (status === 'failed') notes = String(r.error || 'Failed');
          else if (status === 'canceled') notes = 'Canceled';
          else if (status === 'completed') notes = 'Processed';
          else notes = 'In progress';
          return `<tr><td>#${Number(r.id || 0)}</td><td>${escapeHtml(fname)}</td><td>${escapeHtml(detected)}</td><td>${escapeHtml(status)}</td><td>${escapeHtml(progress)}</td><td>${escapeHtml(notes)}</td></tr>`;
        }).join('') +
        '</tbody></table>';
    }
    const active = rows.filter((r) => {
      const s = String(r.status || '');
      return s === 'queued' || s === 'running' || s === 'paused';
    });
    if (active.length) {
      btn.disabled = true;
      btn.textContent = `Processing... (${active.length} active)`;
      const lines = active
        .sort((a, b) => Number(a.id || 0) - Number(b.id || 0))
        .map((r) => `#${r.id} ${String(r.status || '-')} ${Number(r.progress || 0)}% • ${String(r.current_step || '-')}`);
      live.textContent = lines.join('\n');
      const running = active.filter((r) => String(r.status || '') === 'running').length;
      const queued = active.filter((r) => String(r.status || '') === 'queued').length;
      const paused = active.filter((r) => String(r.status || '') === 'paused').length;
      setMsg('msgAutoUpload', `Parsing in progress... running ${running}, queued ${queued}, paused ${paused}.`, true);
      return;
    }
    const completed = rows.filter((r) => String(r.status || '') === 'completed').length;
    const failed = rows.filter((r) => String(r.status || '') === 'failed').length;
    const canceled = rows.filter((r) => String(r.status || '') === 'canceled').length;
    btn.disabled = false;
    btn.textContent = 'Process Documents (Auto-detect)';
    live.textContent = `Completed ${completed}, failed ${failed}, canceled ${canceled} (runs: ${tracked.join(', ')}).`;
    setMsg('msgAutoUpload', `Auto-detect upload finished. completed ${completed}, failed ${failed}, canceled ${canceled}.`, failed === 0);
  }

  function renderSimpleResults() {
    const selectedJob = Number(q('simpleJobSelect').value);
    const allRows = state.matches.filter((m) => !selectedJob || Number(m.job_id) === selectedJob);
    const rows = allRows;
    let mismatchedRows = [];
    if (selectedJob) {
      const job = state.jobs.find((j) => Number(j.id) === selectedJob);
      const jdTags = (job && job.tags) ? job.tags.map((t) => String(t).trim().toLowerCase()).filter(Boolean) : [];
      if (jdTags.length) {
        mismatchedRows = allRows.filter((m) => {
          const resume = state.resumes.find((r) => Number(r.id) === Number(m.resume_id));
          const rsTags = (resume && resume.tags) ? resume.tags.map((t) => String(t).trim().toLowerCase()).filter(Boolean) : [];
          return !jdTags.some((t) => rsTags.includes(t));
        }).map((m) => {
          const resume = state.resumes.find((r) => Number(r.id) === Number(m.resume_id));
          const resumeTags = (resume && resume.tags) ? resume.tags.map((t) => String(t).trim()).filter(Boolean) : [];
          return { ...m, resume_tags_text: resumeTags.length ? resumeTags.join(', ') : '(none)' };
        });
      }
    }
    const byScoreDesc = (a, b) => {
      const sa = Number(a && a.match_score ? a.match_score : 0);
      const sb = Number(b && b.match_score ? b.match_score : 0);
      if (sb !== sa) return sb - sa;
      return String(a && a.candidate_name ? a.candidate_name : '').localeCompare(
        String(b && b.candidate_name ? b.candidate_name : '')
      );
    };
    const deep = rows.filter((m) => String(m.strategy || '') === 'Deep').sort(byScoreDesc);
    const std = rows.filter((m) => String(m.strategy || '') !== 'Deep').sort(byScoreDesc);

    q('simpleTotal').textContent = String(rows.length);
    q('simpleDeepCount').textContent = String(deep.length);
    q('simpleStdCount').textContent = String(std.length);
    if (q('simpleResultScope')) {
      if (!selectedJob) {
        q('simpleResultScope').textContent = 'Showing all saved matches.';
      } else {
        q('simpleResultScope').textContent = 'Showing all saved matches for selected JD (including historical).';
      }
    }

    const renderTable = (arr) => `<table><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th><th>Action</th></tr></thead><tbody>` +
      arr.map((r) => `<tr style="cursor:pointer" onclick="showSimpleMatch(${r.id})"><td>${r.candidate_name || ''}</td><td>${renderScoreCell(r)}</td><td>${decisionBadge(r.decision)}</td><td>${r.reasoning || ''}</td><td><button class="secondary" data-job="${Number(r.job_id || 0)}" data-resume="${Number(r.resume_id || 0)}" data-candidate="${encodeURIComponent(String(r.candidate_name || 'candidate'))}" onclick="event.stopPropagation(); deletePairMatchesFromRow(this)">Delete</button></td></tr>`).join('') +
      `</tbody></table>`;

    q('simpleDeepTable').innerHTML = renderTable(deep);
    q('simpleStdTable').innerHTML = renderTable(std);
    populateSimpleEvidenceSelector(rows);

    const mismatchSection = q('simpleTagMismatchSection');
    const mismatchCaption = q('simpleTagMismatchCaption');
    const mismatchTable = q('simpleTagMismatchTable');
    if (mismatchSection && mismatchCaption && mismatchTable) {
      if (!selectedJob || !mismatchedRows.length) {
        mismatchSection.style.display = 'none';
        mismatchCaption.textContent = '';
        mismatchTable.innerHTML = '';
      } else {
        const byScoreDesc = (a, b) => {
          const sa = Number(a && a.match_score ? a.match_score : 0);
          const sb = Number(b && b.match_score ? b.match_score : 0);
          if (sb !== sa) return sb - sa;
          return String(a && a.candidate_name ? a.candidate_name : '').localeCompare(
            String(b && b.candidate_name ? b.candidate_name : '')
          );
        };
        const sortedMismatch = mismatchedRows.slice().sort(byScoreDesc);
        mismatchSection.style.display = 'block';
        mismatchCaption.textContent = `${sortedMismatch.length} resume(s) in this JD result set do not share any tag with the selected JD.`;
        mismatchTable.innerHTML =
          `<table><thead><tr><th>Candidate</th><th>Resume Tags</th><th>Score</th><th>Decision</th><th>Action</th></tr></thead><tbody>` +
          sortedMismatch.map((r) =>
            `<tr>
              <td>${escapeHtml(r.candidate_name || '')}</td>
              <td>${escapeHtml(r.resume_tags_text || '(none)')}</td>
              <td><b>${Number(r.match_score || 0)}%</b></td>
              <td>${decisionBadge(r.decision)}</td>
              <td><button class="secondary" data-job="${Number(r.job_id || 0)}" data-resume="${Number(r.resume_id || 0)}" data-candidate="${encodeURIComponent(String(r.candidate_name || 'candidate'))}" onclick="deletePairMatchesFromRow(this)">Delete</button></td>
            </tr>`
          ).join('') +
          `</tbody></table>`;
      }
    }
  }

  function populateSimpleEvidenceSelector(rows) {
    const sel = q('simpleEvidenceSelect');
    if (!sel) return;
    const allRows = Array.isArray(rows) ? rows : [];
    if (!allRows.length) {
      sel.innerHTML = '<option value="">No candidates in selected JD</option>';
      q('simpleMatchDetail').textContent = 'Select a row to inspect.';
      return;
    }
    const prev = String(sel.value || '');
    sel.innerHTML = '<option value="">Select candidate</option>' +
      allRows.map((r) => {
        const job = (state.jobs || []).find((j) => Number(j.id) === Number(r.job_id));
        const jobName = String((job && job.filename) || '').trim();
        return `<option value="${r.id}">${escapeHtml(r.candidate_name || 'Unknown')} | ${escapeHtml(jobName)} | ${Number(r.match_score || 0)}%</option>`;
      }).join('');
    if (state.selectedSimpleMatchId && allRows.some((r) => Number(r.id) === Number(state.selectedSimpleMatchId))) {
      sel.value = String(state.selectedSimpleMatchId);
    } else if (prev && allRows.some((r) => String(r.id) === prev)) {
      sel.value = prev;
    }
  }

  async function onSimpleEvidenceSelect() {
    const id = Number((q('simpleEvidenceSelect') && q('simpleEvidenceSelect').value) || 0);
    if (!id) return;
    await showSimpleMatch(id);
  }

  async function queueSimpleSingleRerun() {
    try {
      const matchId = Number((q('simpleEvidenceSelect') && q('simpleEvidenceSelect').value) || 0);
      if (!matchId) throw new Error('Select candidate');
      const row = (state.matches || []).find((r) => Number(r.id) === matchId);
      if (!row) throw new Error('Selected candidate was not found.');
      const cfg = getLegacyRerunConfig();
      const run = await send('/v1/runs', 'POST', {
        job_type: 'score_match',
        payload: {
          job_id: Number(row.job_id),
          resume_id: Number(row.resume_id),
          threshold: cfg.threshold,
          auto_deep: cfg.autoDeep,
          run_name: cfg.runName || `Rerun Single: ${row.candidate_name || 'Candidate'}`,
          force_rerun_pass1: cfg.forcePass1,
          force_rerun_deep: cfg.forceDeep,
          deep_single_prompt: cfg.deepSinglePrompt,
          ai_concurrency: cfg.aiConcurrency,
        },
      });
      state.logPinnedRunId = null;
      q('selectedRunId').value = String(run.id);
      setTrackedBatchRunIds([Number(run.id)]);
      startAnalysisAutoPoll();
      await refreshRunPanels();
      await loadLogs(run.id);
      setMsg('msgMatch', `Queued single rerun as run #${run.id}.`);
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  async function deletePairMatchesFromRow(btn) {
    try {
      const jobId = Number((btn && btn.dataset && btn.dataset.job) || 0);
      const resumeId = Number((btn && btn.dataset && btn.dataset.resume) || 0);
      const candidate = decodeURIComponent(String((btn && btn.dataset && btn.dataset.candidate) || 'candidate'));
      if (!jobId) throw new Error('Select a job first.');
      if (!resumeId) throw new Error('Invalid JD × Resume pair.');
      const ok = await openConfirmModal({
        title: 'Delete JD × Resume Matches',
        message: `Delete all historical matches for JD × Resume pair for "${candidate}"? This cannot be undone.`,
        confirmText: 'Delete',
      });
      if (!ok) return;
      const resp = await send(`/v1/matches/by-pair?job_id=${jobId}&resume_id=${resumeId}`, 'DELETE', null);
      await refreshAll();
      setMsg('msgMatch', `Deleted ${resp.deleted_matches || 0} match row(s) and ${resp.deleted_links || 0} run-link row(s).`);
      renderSimpleResults();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  function renderLegacyRunResults() {
    const rows = state.legacyRunResults || [];
    const jobNames = Array.from(new Set(rows.map((r) => String(r.job_name || '').trim()).filter(Boolean)));
    const primaryJob = jobNames.length ? jobNames[0] : '';
    const jobSummary = jobNames.length === 0
      ? 'No JD data'
      : (jobNames.length === 1 ? primaryJob : `${jobNames.length} JDs (${jobNames.slice(0, 3).join(', ')}${jobNames.length > 3 ? ', ...' : ''})`);
    const byScoreDesc = (a, b) => {
      const sa = Number(a && a.match_score ? a.match_score : 0);
      const sb = Number(b && b.match_score ? b.match_score : 0);
      if (sb !== sa) return sb - sa;
      return String(a && a.candidate_name ? a.candidate_name : '').localeCompare(
        String(b && b.candidate_name ? b.candidate_name : '')
      );
    };
    const deep = rows.filter((r) => String(r.strategy || '') === 'Deep').sort(byScoreDesc);
    const std = rows.filter((r) => String(r.strategy || '') !== 'Deep').sort(byScoreDesc);

    q('runTotal').textContent = String(rows.length);
    q('runDeepCount').textContent = String(deep.length);
    q('runStdCount').textContent = String(std.length);
    q('runUniqueCandidates').textContent = String(new Set(rows.map((r) => r.candidate_name || '')).size);
    q('runUniqueJobs').textContent = String(jobNames.length);
    if (q('legacyRunJobsCaption')) q('legacyRunJobsCaption').textContent = `JD Scope: ${jobSummary}`;
    if (q('legacyDeepHeading')) q('legacyDeepHeading').textContent = jobNames.length === 1
      ? `✨ Deep Matches for ${primaryJob}`
      : `✨ Deep Matches for ${jobSummary}`;
    if (q('legacyStdHeading')) q('legacyStdHeading').textContent = jobNames.length === 1
      ? `🧠 Standard Matches (Pass 1 Only) for ${primaryJob}`
      : `🧠 Standard Matches (Pass 1 Only) for ${jobSummary}`;

    const tableHTML = (arr) => `<table><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th></tr></thead><tbody>` +
      arr.map((r) => `<tr style="cursor:pointer" onclick="showLegacyMatch(${r.id})"><td>${r.candidate_name || ''}</td><td>${renderScoreCell(r)}</td><td>${decisionBadge(r.decision || '')}</td><td>${r.reasoning || ''}</td></tr>`).join('') +
      `</tbody></table>`;

    q('legacyDeepTable').innerHTML = tableHTML(deep);
    q('legacyStdTable').innerHTML = tableHTML(std);
    populateLegacyRerunCandidates();
  }

  function populateLegacyRerunDefaults(meta = null) {
    const runMeta = meta || state.legacyRuns.find((r) => Number(r.id) === Number(state.selectedLegacyRunId));
    if (!runMeta) return;
    const defaultName = `Rerun of ${runMeta.name || `Run ${runMeta.id}`}`;
    const nameEl = q('legacyRerunName');
    if (nameEl && (!nameEl.value || nameEl.value.startsWith('Rerun of '))) {
      nameEl.value = defaultName;
    }
    const threshold = Number(runMeta.threshold || 50);
    if (q('legacyRerunThreshold')) q('legacyRerunThreshold').value = String(threshold);
    if (q('legacyRerunThresholdValue')) q('legacyRerunThresholdValue').textContent = String(threshold);
  }

  function populateLegacyRerunCandidates() {
    const sel = q('legacySingleRerunMatch');
    if (!sel) return;
    const rows = state.legacyRunResults || [];
    if (!rows.length) {
      sel.innerHTML = '<option value="">No candidates in selected run</option>';
      return;
    }
    const prev = sel.value;
    sel.innerHTML = '<option value="">Select candidate</option>' +
      rows.map((r) => `<option value="${r.id}">${r.candidate_name || 'Unknown'} | ${r.job_name || ''} | ${r.match_score || 0}%</option>`).join('');
    if (state.selectedLegacyMatchId && rows.some((r) => Number(r.id) === Number(state.selectedLegacyMatchId))) {
      sel.value = String(state.selectedLegacyMatchId);
      return;
    }
    if (prev && rows.some((r) => String(r.id) === String(prev))) sel.value = prev;
  }

  async function onLegacyCandidateSelect() {
    const matchId = Number(q('legacySingleRerunMatch').value || 0);
    if (!matchId) return;
    await showLegacyMatch(matchId);
  }

  function syncAnalysisDeepForce() {
    const forceDeep = q('forceRerunDeep');
    const autoDeep = q('autoDeep');
    if (!forceDeep || !autoDeep) return;
    if (forceDeep.checked) autoDeep.checked = true;
  }

  function syncLegacyDeepForce() {
    const forceDeep = q('legacyRerunForceDeep');
    const autoDeep = q('legacyRerunAutoDeep');
    if (!forceDeep || !autoDeep) return;
    if (forceDeep.checked) autoDeep.checked = true;
  }

  function getLegacyRerunConfig() {
    syncLegacyDeepForce();
    return {
      threshold: Number(q('legacyRerunThreshold').value || 50),
      autoDeep: !!q('legacyRerunAutoDeep').checked,
      autoTag: !!q('legacyRerunMatchTags').checked,
      forcePass1: !!q('legacyRerunForcePass1').checked,
      forceDeep: !!q('legacyRerunForceDeep').checked,
      deepSinglePrompt: !!(q('legacyRerunDeepSinglePrompt') && q('legacyRerunDeepSinglePrompt').checked),
      aiConcurrency: Math.max(1, Number(q('aiConcurrencyInput')?.value || 1)),
      runName: (q('legacyRerunName').value || '').trim() || null,
    };
  }

  async function createLegacyRun(name, threshold) {
    const payload = {
      name: String(name || '').trim(),
      threshold: Number(threshold || 50),
    };
    if (!payload.name) throw new Error('Run name is required.');
    return send('/v1/runs/legacy', 'POST', payload);
  }

  async function queueLegacyBatchRerun() {
    try {
      const rows = state.legacyRunResults || [];
      if (!rows.length) throw new Error('No results in selected run batch.');
      const cfg = getLegacyRerunConfig();
      const selectedLegacyRunId = Number(q('legacyRunSelect').value || 0);
      const selectedLegacyMeta = (state.legacyRuns || []).find((r) => Number(r.id) === selectedLegacyRunId) || null;
      const defaultName = selectedLegacyMeta && selectedLegacyMeta.name
        ? String(selectedLegacyMeta.name).replace(/^Auto:\s*/i, 'Run: ')
        : 'Run: Batch Rerun';
      const legacyRun = await createLegacyRun(cfg.runName || defaultName, cfg.threshold);
      let queued = 0;
      const runIds = [];
      const seen = new Set();
      for (const row of rows) {
        const key = `${row.job_id}:${row.resume_id}`;
        if (seen.has(key)) continue;
        seen.add(key);
        if (cfg.autoTag) {
          const job = state.jobs.find((j) => Number(j.id) === Number(row.job_id));
          const resume = state.resumes.find((r) => Number(r.id) === Number(row.resume_id));
          const jdTags = (job && job.tags) ? job.tags.map((t) => String(t).trim()).filter(Boolean) : [];
          const rsTags = (resume && resume.tags) ? resume.tags.map((t) => String(t).trim()) : [];
          if (jdTags.length && !jdTags.some((t) => rsTags.includes(t))) {
            continue;
          }
        }
        const run = await send('/v1/runs', 'POST', {
          job_type: 'score_match',
          payload: {
            job_id: Number(row.job_id),
            resume_id: Number(row.resume_id),
            threshold: cfg.threshold,
            auto_deep: cfg.autoDeep,
            run_name: cfg.runName || null,
            legacy_run_id: Number(legacyRun.id),
            force_rerun_pass1: cfg.forcePass1,
            force_rerun_deep: cfg.forceDeep,
            deep_single_prompt: cfg.deepSinglePrompt,
            ai_concurrency: cfg.aiConcurrency,
          },
        });
        queued += 1;
        runIds.push(Number(run.id));
      }
      if (queued === 0) throw new Error('No rerun tasks were queued.');
      state.logPinnedRunId = null;
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
      await refreshRunPanels();
      setMsg('msgLegacyRerun', `Queued batch rerun: ${queued} task(s), queue run #${runIds.join(', ')} linked to legacy run #${legacyRun.id}.`);
    } catch (e) {
      setMsg('msgLegacyRerun', e.message, false);
    }
  }

  async function queueLegacySingleRerun() {
    try {
      const matchId = Number(q('legacySingleRerunMatch').value || 0);
      if (!matchId) throw new Error('Select a candidate for single rerun.');
      const row = (state.legacyRunResults || []).find((r) => Number(r.id) === matchId);
      if (!row) throw new Error('Selected candidate was not found in current run.');
      const cfg = getLegacyRerunConfig();
      const run = await send('/v1/runs', 'POST', {
        job_type: 'score_match',
        payload: {
          job_id: Number(row.job_id),
          resume_id: Number(row.resume_id),
          threshold: cfg.threshold,
          auto_deep: cfg.autoDeep,
          run_name: cfg.runName || `Rerun Single: ${row.candidate_name || row.resume_name || 'Candidate'}`,
          force_rerun_pass1: cfg.forcePass1,
          force_rerun_deep: cfg.forceDeep,
          deep_single_prompt: cfg.deepSinglePrompt,
          ai_concurrency: cfg.aiConcurrency,
        },
      });
      state.logPinnedRunId = null;
      q('selectedRunId').value = String(run.id);
      setTrackedBatchRunIds([Number(run.id)]);
      startAnalysisAutoPoll();
      await refreshRunPanels();
      await loadLogs(run.id);
      setMsg('msgLegacyRerun', `Queued single rerun as run #${run.id}.`);
    } catch (e) {
      setMsg('msgLegacyRerun', e.message, false);
    }
  }

  async function refreshAll() {
    const [dash, jobs, resumes, tags, matches, runs, legacyRuns] = await Promise.all([
      getJson('/v1/dashboard'),
      getJson('/v1/jobs'),
      getJson('/v1/resumes'),
      getJson('/v1/tags'),
      getJson('/v1/matches'),
      getJson('/v1/runs'),
      getJson('/v1/runs/legacy'),
    ]);

    state.jobs = jobs;
    state.resumes = resumes;
    state.tags = tags;
    state.matches = matches;
    state.runs = runs;
    state.legacyRuns = legacyRuns;

    const prevRunId = state.selectedLegacyRunId || q('legacyRunSelect').value;
    q('legacyRunSelect').innerHTML = '<option value="">Select</option>' + legacyRuns.map((r) => `<option value="${r.id}">${r.name} (${r.created_at})</option>`).join('');
    if (prevRunId && legacyRuns.some((r) => String(r.id) === String(prevRunId))) {
      q('legacyRunSelect').value = String(prevRunId);
    } else if (!q('legacyRunSelect').value && legacyRuns.length > 0) {
      q('legacyRunSelect').value = String(legacyRuns[0].id);
    }

    const c = dash.counts || {};
    q('legacyRunCaption').textContent = '';

    renderJobs();
    renderResumes();
    renderTags();
    renderRuns();
    renderAnalysisSelectors();
    renderSimpleResults();
    await loadLegacyRunResults(true);
    renderUnifiedDataBrowser();
    updateAnalysisQueueMessage();
    const hasActiveQueue = (state.runs || []).some((r) => r.status === 'queued' || r.status === 'running');
    if (hasActiveQueue) startAnalysisAutoPoll();
    else stopAnalysisAutoPoll();
  }

  function runSignature(rows) {
    return (rows || [])
      .map((r) => `${r.id}:${r.status}:${r.progress || 0}:${r.current_step || ''}`)
      .join('|');
  }

  async function pollRunActivity() {
    if (!state.analysisAutoPollEnabled) return;

    const previousRuns = state.runs || [];
    const hadActive = previousRuns.some((r) => r.status === 'queued' || r.status === 'running');
    const previousById = new Map(previousRuns.map((r) => [Number(r.id), r]));

    const runs = await getJson('/v1/runs');
    const hasActive = runs.some((r) => r.status === 'queued' || r.status === 'running');
    const runChanged = runSignature(previousRuns) !== runSignature(runs);

    state.runs = runs;
    renderRuns();
    updateAnalysisQueueMessage();
    const trackedReprocessRunId = Number(state.reprocessRunId || 0);
    if (trackedReprocessRunId) {
      const reprocessRun = runs.find((r) => Number(r.id) === trackedReprocessRunId) || null;
      if (reprocessRun) {
        const status = String(reprocessRun.status || '');
        const filename = reprocessRun && reprocessRun.payload ? String(reprocessRun.payload.filename || '') : '';
        if (status === 'queued' || status === 'running' || status === 'paused') {
          setMsg('msgUnifiedEdit', `Reprocess run #${trackedReprocessRunId} is ${status}${filename ? ` for ${filename}` : ''}.`);
        } else if (status === 'completed') {
          setMsg('msgUnifiedEdit', `Reprocess run #${trackedReprocessRunId} completed.`);
          state.reprocessRunId = null;
          if (state.selectedUnifiedId) {
            await openUnifiedDataRecord(Number(state.selectedUnifiedId), true);
          }
        } else if (status === 'failed' || status === 'canceled') {
          const err = String(reprocessRun.error || '').trim();
          setMsg('msgUnifiedEdit', `Reprocess run #${trackedReprocessRunId} ${status}.${err ? ` ${err}` : ''}`, false);
          state.reprocessRunId = null;
        }
      }
    }
    const pauseSettleRunId = Number(state.pauseSettleRunId || 0);
    if (pauseSettleRunId) {
      const settleRun = runs.find((r) => Number(r.id) === pauseSettleRunId) || null;
      const stillPendingPause = !!(
        settleRun &&
        (isPauseRequested(settleRun) || String(settleRun.status || '') === 'running')
      );
      if (!stillPendingPause) {
        state.pauseSettleRunId = null;
      }
    }
    if (!state.pauseSettleRunId && isQueuePausedByRuns(runs)) {
      stopAnalysisAutoPoll();
      return;
    }
    if (!state.pauseSettleRunId && !hasLiveQueueRuns(runs)) {
      stopAnalysisAutoPoll();
      return;
    }

    const pinnedRunId = getPinnedRunId();
    if (pinnedRunId) {
      await loadLogs(pinnedRunId);
    } else {
      const newlyRunning = runs
        .filter((r) => {
          const prev = previousById.get(Number(r.id));
          return r.status === 'running' && (!prev || prev.status !== 'running');
        })
        .sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
      const running = runs
        .filter((r) => r.status === 'running')
        .sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
      const paused = runs
        .filter((r) => r.status === 'paused')
        .sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
      const queued = runs
        .filter((r) => r.status === 'queued')
        .sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
      const followRun = newlyRunning[0] || running[0] || paused[0] || queued[0] || null;
      if (followRun) {
        const sel = q('selectedRunId');
        if (sel && Array.from(sel.options).some((o) => String(o.value) === String(followRun.id))) {
          sel.value = String(followRun.id);
        }
        await loadLogs(Number(followRun.id));
      } else {
        const historyRaw = String((q('historyRunId') && q('historyRunId').value) || '').trim();
        if (historyRaw) {
          await loadHistoryLogs();
        }
      }
    }

    if (!runChanged) return;

    // Refresh heavy datasets only when a run transitions from active -> terminal.
    const transitioned = runs.filter((r) => {
      const prev = previousById.get(Number(r.id));
      if (!prev) return false;
      const prevActive = prev.status === 'queued' || prev.status === 'running' || prev.status === 'paused';
      const nowTerminal = r.status === 'completed' || r.status === 'failed' || r.status === 'canceled';
      return prevActive && nowTerminal;
    });

    const affectsDataJobType = (r) =>
      r.job_type === 'ingest_job' ||
      r.job_type === 'ingest_resume' ||
      r.job_type === 'ingest_job_file' ||
      r.job_type === 'ingest_resume_file' ||
      r.job_type === 'ingest_auto_file' ||
      r.job_type === 'reprocess_job' ||
      r.job_type === 'reprocess_resume' ||
      r.job_type === 'score_match';

    const transitionedAffectsData = transitioned.some(affectsDataJobType);
    const fastTerminalAffectsData = runs.some((r) => {
      const prev = previousById.get(Number(r.id));
      if (prev) return false;
      const nowTerminal = r.status === 'completed' || r.status === 'failed' || r.status === 'canceled';
      return nowTerminal && affectsDataJobType(r);
    });

    if (transitionedAffectsData || fastTerminalAffectsData || hadActive !== hasActive) {
      await refreshAll();
    }

    if (!hasActive) {
      stopAnalysisAutoPoll();
    }
  }

  async function refreshRunPanels() {
    const runs = await getJson('/v1/runs');
    state.runs = runs;
    renderRuns();
    updateAnalysisQueueMessage();
    const pinnedRunId = getPinnedRunId();
    if (pinnedRunId) {
      await loadLogs(pinnedRunId);
      return;
    }
    const running = runs
      .filter((r) => r.status === 'running')
      .sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
    const paused = runs
      .filter((r) => r.status === 'paused')
      .sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
    const queued = runs
      .filter((r) => r.status === 'queued')
      .sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
    const followRun = running[0] || paused[0] || queued[0] || null;
    if (followRun) {
      const sel = q('selectedRunId');
      if (sel && Array.from(sel.options).some((o) => String(o.value) === String(followRun.id))) {
        sel.value = String(followRun.id);
      }
      return loadLogs(Number(followRun.id));
    }
    const historyRaw = String((q('historyRunId') && q('historyRunId').value) || '').trim();
    if (historyRaw) return loadHistoryLogs();
  }

  async function loadLegacyRunResults(preserveSelection = false) {
    const runId = Number(q('legacyRunSelect').value);
    state.selectedLegacyRunId = runId || null;
    if (!runId) {
      state.legacyRunResults = [];
      state.selectedLegacyMatchId = null;
      renderLegacyRunResults();
      q('legacyRunCaption').textContent = '';
      if (q('legacyRunJobsCaption')) q('legacyRunJobsCaption').textContent = '';
      q('legacyMatchDetail').textContent = 'Select a row to inspect.';
      q('legacyDeepHeading').textContent = '✨ Deep Matches for Selected Run';
      if (q('legacyStdHeading')) q('legacyStdHeading').textContent = '🧠 Standard Matches (Pass 1 Only)';
      q('legacySingleRerunMatch').innerHTML = '<option value="">No candidates in selected run</option>';
      setMsg('msgLegacyRerun', '');
      return;
    }
    state.legacyRunResults = await getJson(`/v1/runs/legacy/${runId}/results`);
    const meta = state.legacyRuns.find((r) => Number(r.id) === runId);
    q('legacyRunCaption').textContent = meta ? `Results showing against Deep Match Threshold of ${meta.threshold}% used in this run.` : '';
    if (q('legacyRunJobsCaption')) q('legacyRunJobsCaption').textContent = '';
    q('legacyDeepHeading').textContent = '✨ Deep Matches for Selected Run';
    if (q('legacyStdHeading')) q('legacyStdHeading').textContent = '🧠 Standard Matches (Pass 1 Only)';
    populateLegacyRerunDefaults(meta || null);
    renderLegacyRunResults();

    if (preserveSelection && state.selectedLegacyMatchId) {
      const exists = state.legacyRunResults.some((r) => Number(r.id) === Number(state.selectedLegacyMatchId));
      if (exists) {
        await showLegacyMatch(state.selectedLegacyMatchId, true);
        return;
      }
    }

    state.selectedLegacyMatchId = null;
    q('legacyMatchDetail').textContent = 'Select a row to inspect.';
  }

  function closeLegacyActionsMenu() {
    const menu = q('legacyActionsMenu');
    if (menu) menu.open = false;
  }

  function onTextPromptBackdropClick(ev) {
    if (ev && ev.target && ev.target.id === 'textPromptModal') {
      closeTextPrompt(null);
    }
  }

  function openTextPrompt(opts = {}) {
    const modal = q('textPromptModal');
    const input = q('textPromptInput');
    const title = q('textPromptTitle');
    const label = q('textPromptLabel');
    const confirmBtn = q('textPromptConfirm');
    if (!modal || !input || !title || !label || !confirmBtn) return Promise.resolve(null);
    title.textContent = String(opts.title || 'Enter value');
    label.textContent = String(opts.label || 'Value');
    input.placeholder = String(opts.placeholder || '');
    input.value = String(opts.value || '');
    confirmBtn.textContent = String(opts.confirmText || 'Save');
    modal.classList.add('show');
    setTimeout(() => {
      input.focus();
      input.select();
    }, 0);
    return new Promise((resolve) => {
      textPromptResolver = resolve;
      input.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          confirmTextPrompt();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          closeTextPrompt(null);
        }
      };
    });
  }

  function closeTextPrompt(result) {
    const modal = q('textPromptModal');
    const input = q('textPromptInput');
    if (modal) modal.classList.remove('show');
    if (input) input.onkeydown = null;
    const resolve = textPromptResolver;
    textPromptResolver = null;
    if (resolve) resolve(result);
  }

  function confirmTextPrompt() {
    const input = q('textPromptInput');
    closeTextPrompt(input ? input.value : '');
  }

  function onConfirmBackdropClick(ev) {
    if (ev && ev.target && ev.target.id === 'confirmModal') {
      closeConfirmModal(false);
    }
  }

  function openConfirmModal(opts = {}) {
    const modal = q('confirmModal');
    const title = q('confirmTitle');
    const message = q('confirmMessage');
    const okBtn = q('confirmOkBtn');
    if (!modal || !title || !message || !okBtn) return Promise.resolve(false);
    title.textContent = String(opts.title || 'Confirm Action');
    message.textContent = String(opts.message || 'Are you sure?');
    okBtn.textContent = String(opts.confirmText || 'Confirm');
    modal.classList.add('show');
    return new Promise((resolve) => {
      confirmModalResolver = resolve;
      document.addEventListener('keydown', onConfirmEscape);
    });
  }

  function onConfirmEscape(e) {
    if (e.key !== 'Escape') return;
    e.preventDefault();
    closeConfirmModal(false);
  }

  function closeConfirmModal(result) {
    const modal = q('confirmModal');
    if (modal) modal.classList.remove('show');
    document.removeEventListener('keydown', onConfirmEscape);
    const resolve = confirmModalResolver;
    confirmModalResolver = null;
    if (resolve) resolve(!!result);
  }

  async function deleteLegacyRunBatch() {
    try {
      const runId = Number((q('legacyRunSelect') && q('legacyRunSelect').value) || 0);
      if (!runId) throw new Error('Select a run batch first.');
      const deleteLinked = !!(q('legacyDeleteWithMatches') && q('legacyDeleteWithMatches').checked);
      const msg = deleteLinked
        ? 'Delete this batch and all matches linked to it? This cannot be undone.'
        : 'Delete this batch record only? Linked matches will remain.';
      const ok = await openConfirmModal({ title: 'Delete Run Batch', message: msg, confirmText: 'Delete' });
      if (!ok) return;
      const resp = await send(`/v1/runs/legacy/${runId}?delete_linked_matches=${deleteLinked ? 'true' : 'false'}`, 'DELETE', null);
      setMsg('msgLegacyRerun', `Batch deleted. Links removed: ${resp.deleted_links || 0}; matches removed: ${resp.deleted_matches || 0}.`);
      closeLegacyActionsMenu();
      await refreshAll();
    } catch (e) {
      setMsg('msgLegacyRerun', e.message, false);
    }
  }

  async function renameLegacyRunBatch() {
    try {
      const runId = Number((q('legacyRunSelect') && q('legacyRunSelect').value) || 0);
      if (!runId) throw new Error('Select a run batch first.');
      const current = (state.legacyRuns || []).find((r) => Number(r.id) === runId) || null;
      const proposed = await openTextPrompt({
        title: 'Rename Run Batch',
        label: 'Run name',
        placeholder: 'Enter run name',
        value: String((current && current.name) || ''),
        confirmText: 'Save Name',
      });
      if (proposed === null) return;
      const name = String(proposed || '').trim();
      if (!name) throw new Error('Run name is required.');
      await send(`/v1/runs/legacy/${runId}/name`, 'PUT', { name });
      setMsg('msgLegacyRerun', `Run name updated to "${name}".`);
      closeLegacyActionsMenu();
      await refreshAll();
      if (q('legacyRunSelect')) q('legacyRunSelect').value = String(runId);
      await loadLegacyRunResults(true);
    } catch (e) {
      setMsg('msgLegacyRerun', e.message, false);
    }
  }

  function downloadLegacyCsv() {
    const rows = state.legacyRunResults || [];
    if (!rows.length) {
      setMsg('msgLegacyRerun', 'No rows available for export.', false);
      return;
    }
    const header = ['id', 'candidate_name', 'job_name', 'resume_name', 'match_score', 'standard_score', 'decision', 'strategy', 'reasoning'];
    const csv = [
      header.join(','),
      ...rows.map((r) =>
        header.map((k) => {
          const v = r[k] === null || r[k] === undefined ? '' : String(r[k]).replaceAll('\"', '\"\"');
          return `\"${v}\"`;
        }).join(',')
      ),
    ].join('\\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const runId = Number(q('legacyRunSelect').value || 0);
    const runMeta = (state.legacyRuns || []).find((r) => Number(r.id) === runId) || null;
    const safeName = String((runMeta && runMeta.name) || `run_${runId || 'selected'}`)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 60) || 'run_selected';
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    a.download = `${safeName}_${stamp}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    closeLegacyActionsMenu();
    setMsg('msgLegacyRerun', `CSV exported (${rows.length} rows).`);
  }

  function downloadLegacyJson() {
    const rows = state.legacyRunResults || [];
    if (!rows.length) {
      setMsg('msgLegacyRerun', 'No rows available for export.', false);
      return;
    }
    const runId = Number(q('legacyRunSelect').value || 0);
    const runMeta = (state.legacyRuns || []).find((r) => Number(r.id) === runId) || null;
    const payload = {
      exported_at: new Date().toISOString(),
      run: runMeta || { id: runId || null },
      total_rows: rows.length,
      results: rows,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const safeName = String((runMeta && runMeta.name) || `run_${runId || 'selected'}`)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 60) || 'run_selected';
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    a.download = `${safeName}_${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    closeLegacyActionsMenu();
    setMsg('msgLegacyRerun', `JSON exported (${rows.length} rows).`);
  }

  async function showLegacyMatch(matchId, preserve = false) {
    try {
      state.selectedLegacyMatchId = Number(matchId);
      if (q('legacySingleRerunMatch')) q('legacySingleRerunMatch').value = String(matchId);
      const d = await getJson(`/v1/matches/${matchId}`);
      renderMatchInvestigatorInto('legacyMatchDetail', d);
    } catch (e) {
      if (!preserve) q('legacyMatchDetail').textContent = e.message;
    }
  }

  async function showSimpleMatch(matchId, preserve = false) {
    try {
      state.selectedSimpleMatchId = Number(matchId);
      if (q('simpleEvidenceSelect')) q('simpleEvidenceSelect').value = String(matchId);
      const d = await getJson(`/v1/matches/${matchId}`);
      renderMatchInvestigatorInto('simpleMatchDetail', d);
    } catch (e) {
      if (!preserve) q('simpleMatchDetail').textContent = e.message;
    }
  }

  function renderMatchInvestigator(d) {
    const statusClass = (s) => {
      const v = String(s || '').toLowerCase();
      if (v === 'met') return 'met';
      if (v === 'partial') return 'partial';
      return 'missing';
    };
    const details = Array.isArray(d.match_details) ? d.match_details : [];
    const rows = details.map((it) => {
      const category = String(it.category || '').replaceAll('_', ' ').toUpperCase();
      const req = it.requirement || '';
      const ev = it.evidence || it.evidence_found || 'None';
      const st = it.status || 'Missing';
      return `<tr>
        <td>${category}</td>
        <td>${req}</td>
        <td>${ev}</td>
        <td><span class="status-chip ${statusClass(st)}">${st}</span></td>
      </tr>`;
    }).join('');
    const standardScore = (d.standard_score !== null && d.standard_score !== undefined) ? `${d.standard_score}%` : '';
    const standardReasoning = d.standard_reasoning ? `<details class="expander" style="margin-top:8px;"><summary>📄 View Pass 1 (Standard) Analysis</summary><div class="mini-muted row">${d.standard_reasoning}</div></details>` : '';
    return `
      <div class="investigator">
        <div class="investigator-head">
          <div>
            <div class="investigator-name">${d.candidate_name || ''}</div>
            <div class="mini-muted" style="margin-top:6px;">Pass 1 (Standard) Score: ${standardScore}</div>
            ${d.strategy === 'Deep' ? '<div class="mini-muted" style="margin-top:4px;">✨ Evaluated with High-Precision Multi-Pass Tiered Weighting</div>' : ''}
          </div>
          <div class="investigator-score-card">
            <div class="mini-muted" style="text-align:right;">Weighted Score</div>
            <div class="investigator-score">${d.match_score || 0}%</div>
          </div>
        </div>
        <div class="final-decision">Final Decision: ${d.reasoning || ''}</div>
        ${standardReasoning}
        <div style="margin-top:8px;">
          <table>
            <thead><tr><th>Category</th><th>Requirement</th><th>Evidence Found</th><th>Status</th></tr></thead>
            <tbody>${rows || '<tr><td colspan="4">Detailed requirement breakdown unavailable for this match.</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderMatchInvestigatorInto(targetId, detail) {
    const el = q(targetId);
    if (!el) return;
    el.innerHTML = renderMatchInvestigator(detail);
  }

  function renderScoreCell(row) {
    const score = Number((row && row.match_score) || 0);
    const standardScore = (row && row.standard_score !== null && row.standard_score !== undefined)
      ? `${Number(row.standard_score)}%`
      : '';
    return `<b>${score}%</b>` +
      (standardScore ? `<span class="score-sub">Pass 1: ${standardScore}</span>` : '');
  }

  async function queueIngestJob() {
    try {
      const tags = tagsFrom(q('jdTagsCsv').value);
      const fileInput = q('jdFileUpload');
      const files = Array.from((fileInput && fileInput.files) || []);
      const forceReparse = !!q('jdForceReparse').checked;
      if (!files.length) throw new Error('Upload at least one JD file.');

      const runIds = [];
      for (const f of files) {
        const existing = state.jobs.find((j) => String(j.filename) === String(f.name));
        if (existing && !forceReparse) continue;
        const bytes = new Uint8Array(await f.arrayBuffer());
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        const content_b64 = btoa(binary);
        const run = await send('/v1/runs', 'POST', {
          job_type: 'ingest_job_file',
          payload: { filename: f.name, content_b64, tags, force_reparse: forceReparse },
        });
        runIds.push(Number(run.id));
      }
      if (!runIds.length) throw new Error('All uploaded JDs already exist. Enable Force Reparse to process them again.');
      setMsg('msgJD', `Queued ${runIds.length} JD parsing run(s): #${runIds.join(', ')}`);
      q('selectedRunId').value = String(runIds[runIds.length - 1]);
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
      await refreshAll();
    } catch (e) {
      setMsg('msgJD', e.message, false);
    }
  }

  async function queueIngestAuto() {
    state.autoUploadSubmitting = true;
    updateAutoUploadStatus();
    try {
      const tags = tagsFrom(q('autoTagsCsv').value);
      const selectedTag = String((q('autoTagAssign') && q('autoTagAssign').value) || '').trim();
      if (selectedTag && !tags.includes(selectedTag)) tags.push(selectedTag);
      const fileInput = q('autoFileUpload');
      const files = Array.from((fileInput && fileInput.files) || []);
      const forceReparse = !!q('autoForceReparse').checked;
      if (!files.length) throw new Error('Upload at least one document file.');
      const existingNames = new Set([
        ...(state.jobs || []).map((j) => String(j.filename || '')),
        ...(state.resumes || []).map((r) => String(r.filename || '')),
      ]);

      const runIds = [];
      const skippedExisting = [];
      for (const f of files) {
        if (!forceReparse && existingNames.has(String(f.name || ''))) {
          skippedExisting.push(String(f.name || ''));
          continue;
        }
        const bytes = new Uint8Array(await f.arrayBuffer());
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        const content_b64 = btoa(binary);
        const run = await send('/v1/runs', 'POST', {
          job_type: 'ingest_auto_file',
          payload: { filename: f.name, content_b64, tags, force_reparse: forceReparse },
        });
        runIds.push(Number(run.id));
      }
      if (!runIds.length) {
        if (skippedExisting.length) {
          throw new Error(`All selected files already exist (${skippedExisting.length}). Enable "Force Reparse Existing Files" to run AI again.`);
        }
        throw new Error('No files were queued.');
      }
      const skipNote = skippedExisting.length
        ? ` Skipped ${skippedExisting.length} existing file(s): ${skippedExisting.slice(0, 5).join(', ')}${skippedExisting.length > 5 ? ', ...' : ''}.`
        : '';
      setMsg('msgAutoUpload', `Queued ${runIds.length} auto-detect ingest run(s): #${runIds.join(', ')}.${skipNote}`);
      state.autoUploadRunIds = runIds.slice();
      q('selectedRunId').value = String(runIds[runIds.length - 1]);
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
      await refreshAll();
    } catch (e) {
      setMsg('msgAutoUpload', e.message, false);
    } finally {
      state.autoUploadSubmitting = false;
      updateAutoUploadStatus();
    }
  }

  async function queueIngestResume() {
    try {
      const tags = tagsFrom(q('resTagsCsv').value);
      const fileInput = q('resFileUpload');
      const files = Array.from((fileInput && fileInput.files) || []);
      const forceReparse = !!q('resForceReparse').checked;
      if (!files.length) throw new Error('Upload at least one resume file.');

      const runIds = [];
      for (const f of files) {
        const existing = state.resumes.find((r) => String(r.filename) === String(f.name));
        if (existing && !forceReparse) continue;
        const bytes = new Uint8Array(await f.arrayBuffer());
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        const content_b64 = btoa(binary);
        const run = await send('/v1/runs', 'POST', {
          job_type: 'ingest_resume_file',
          payload: { filename: f.name, content_b64, tags, force_reparse: forceReparse },
        });
        runIds.push(Number(run.id));
      }
      if (!runIds.length) throw new Error('All uploaded resumes already exist. Enable Force Reparse to process them again.');
      setMsg('msgRes', `Queued ${runIds.length} resume parsing run(s): #${runIds.join(', ')}`);
      q('selectedRunId').value = String(runIds[runIds.length - 1]);
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
      await refreshAll();
    } catch (e) {
      setMsg('msgRes', e.message, false);
    }
  }

  async function reparseJD() {
    try {
      const scope = q('reparseJdScope').value;
      const ids = scope === 'all'
        ? state.jobs.map((x) => Number(x.id))
        : Array.from(q('reparseJdSelect').selectedOptions).map((o) => Number(o.value)).filter(Boolean);
      if (!ids.length) throw new Error('No JDs selected for reparse.');
      const runIds = [];
      for (const id of ids) {
        const jd = await getJson(`/v1/jobs/${id}`);
        const run = await send('/v1/runs', 'POST', {
          job_type: 'ingest_job',
          payload: { filename: jd.filename, content: jd.content, tags: jd.tags || [] },
        });
        runIds.push(Number(run.id));
      }
      setMsg('msgReparseJD', `Queued JD reparse run(s): #${runIds.join(', ')}`);
      q('selectedRunId').value = String(runIds[runIds.length - 1]);
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
    } catch (e) {
      setMsg('msgReparseJD', e.message, false);
    }
  }

  async function reparseResume() {
    try {
      const scope = q('reparseResScope').value;
      const ids = scope === 'all'
        ? state.resumes.map((x) => Number(x.id))
        : Array.from(q('reparseResSelect').selectedOptions).map((o) => Number(o.value)).filter(Boolean);
      if (!ids.length) throw new Error('No resumes selected for reparse.');
      const runIds = [];
      for (const id of ids) {
        const rs = await getJson(`/v1/resumes/${id}`);
        const run = await send('/v1/runs', 'POST', {
          job_type: 'ingest_resume',
          payload: { filename: rs.filename, content: rs.content, tags: rs.tags || [] },
        });
        runIds.push(Number(run.id));
      }
      setMsg('msgReparseRes', `Queued resume reparse run(s): #${runIds.join(', ')}`);
      q('selectedRunId').value = String(runIds[runIds.length - 1]);
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
    } catch (e) {
      setMsg('msgReparseRes', e.message, false);
    }
  }

  async function addInlineTagToSelect(newTagId, targetSelectId, msgId) {
    try {
      const name = String(q(newTagId).value || '').trim();
      if (!name) throw new Error('Enter tag name');
      await send('/v1/tags', 'POST', { name });
      q(newTagId).value = '';
      await refreshAll();
      const target = q(targetSelectId);
      if (target) target.value = name;
      if (targetSelectId === 'jdTagAssign') addJdUploadTag();
      if (targetSelectId === 'autoTagAssign') addAutoUploadTag();
      if (targetSelectId === 'resTagAssign') addResUploadTag();
      setMsg(msgId, `Tag "${name}" added.`);
    } catch (e) {
      setMsg(msgId, e.message, false);
    }
  }

  async function addInlineTag(newTagId, targetInputId, msgId) {
    try {
      const name = String(q(newTagId).value || '').trim();
      if (!name) throw new Error('Enter tag name');
      await send('/v1/tags', 'POST', { name });
      const current = tagsFrom(q(targetInputId).value);
      if (!current.includes(name)) current.push(name);
      q(targetInputId).value = current.join(', ');
      q(newTagId).value = '';
      await refreshAll();
      setMsg(msgId, `Tag "${name}" added.`);
    } catch (e) {
      setMsg(msgId, e.message, false);
    }
  }

  async function importResumeJson() {
    try {
      const input = q('resJsonImport');
      const file = input && input.files && input.files[0] ? input.files[0] : null;
      if (!file) throw new Error('Choose a JSON file to import.');
      const raw = await file.text();
      const data = JSON.parse(raw);
      if (!Array.isArray(data)) throw new Error('JSON must be an array of resume records.');

      const runIds = [];
      for (const rec of data) {
        const filename = String((rec && rec.filename) || '').trim();
        const content = String((rec && rec.content) || '').trim();
        const profile = rec ? rec.profile : null;
        if (!filename || !content) continue;
        const tags = Array.isArray(rec.tags) ? rec.tags : tagsFrom(String(rec.tags || ''));
        const run = await send('/v1/runs', 'POST', {
          job_type: 'ingest_resume',
          payload: { filename, content, tags, profile },
        });
        runIds.push(Number(run.id));
      }
      if (!runIds.length) throw new Error('No valid records found in JSON.');
      q('selectedRunId').value = String(runIds[runIds.length - 1]);
      setTrackedBatchRunIds(runIds.slice());
      startAnalysisAutoPoll();
      setMsg('msgRes', `Queued ${runIds.length} resume import run(s): #${runIds.join(', ')}`);
      await refreshAll();
    } catch (e) {
      setMsg('msgRes', e.message, false);
    }
  }

  async function queueScoreMatch() {
    const startBtn = q('startAnalysisBtn');
    state.analysisSubmitting = true;
    updateStartAnalysisButtonState();
    try {
      const jobSel = q('matchJobSelect').value;
      const resSel = q('matchResumeSelect').value;
      const autoTag = q('analysisAutoTagMatch') && q('analysisAutoTagMatch').checked;
      setMsg('msgMatch', 'Submitting analysis jobs...', true);

      const jobIds = jobSel === '__all__' ? state.jobs.map((j) => Number(j.id)) : [Number(jobSel)];
      let resumeIds = resSel === '__all__'
        ? Array.from(q('matchResumeSelect').options).map((o) => Number(o.value)).filter((v) => v && v !== Number('__all__'))
        : [Number(resSel)];
      resumeIds = resumeIds.filter(Boolean);

      if (!jobIds.length || !resumeIds.length) throw new Error('Select at least one Job and one Resume');

      const threshold = Number(q('threshold').value || 50);
      syncAnalysisDeepForce();
      const autoDeep = q('autoDeep').checked;
      const runName = q('runName').value.trim() || null;
      const forceRerunPass1 = q('forceRerunPass1').checked;
      const forceRerunDeep = q('forceRerunDeep').checked;
      const deepSinglePrompt = !!(q('deepSinglePrompt') && q('deepSinglePrompt').checked);
      const debugBulkLog = !!(q('debugBulkLog') && q('debugBulkLog').checked);
      const maxDeepPerJd = Math.max(0, Number(q('maxDeepPerJdInput').value || 0));
      const aiConcurrency = Math.max(1, Number(q('aiConcurrencyInput').value || 1));
      const jobConcurrency = Math.max(1, Number(q('jobConcurrencyInput').value || 1));
      await send('/v1/settings/runtime', 'PUT', { job_concurrency: jobConcurrency });

      let queued = 0;
      const queuedRunIds = [];
      let lastRunId = null;
      let firstQueuedRunId = null;
      for (const job_id of jobIds) {
        const job = state.jobs.find((j) => Number(j.id) === Number(job_id));
        const jdTags = (job && job.tags) ? job.tags.map((t) => String(t).trim()).filter(Boolean) : [];
        let perJobResumeIds = resumeIds;
        if (autoTag && jdTags.length) {
          perJobResumeIds = resumeIds.filter((rid) => {
            const r = state.resumes.find((x) => Number(x.id) === Number(rid));
            const rTags = (r && r.tags) ? r.tags.map((t) => String(t).trim()) : [];
            return jdTags.some((t) => rTags.includes(t));
          });
        }

        if (!perJobResumeIds.length) continue;
        const defaultRunName = buildLegacyRunNameForJob(runName || state.lastAutoRunName || '', job);
        const legacyRun = await createLegacyRun(defaultRunName, threshold);
        const batchGroupKey = `legacy:${Number(legacyRun.id)}:job:${Number(job_id)}:cap:${maxDeepPerJd}`;
        const useDeepCapTwoPhase = autoDeep && maxDeepPerJd > 0 && !forceRerunDeep;

        for (const resume_id of perJobResumeIds) {
          const run = await send('/v1/runs', 'POST', {
            job_type: 'score_match',
            payload: {
              job_id,
              resume_id,
              threshold,
              auto_deep: useDeepCapTwoPhase ? false : autoDeep,
              run_name: runName || null,
              legacy_run_id: Number(legacyRun.id),
              force_rerun_pass1: forceRerunPass1,
              force_rerun_deep: forceRerunDeep,
              deep_single_prompt: deepSinglePrompt,
              debug_bulk_log: debugBulkLog,
              max_deep_scans_per_jd: maxDeepPerJd,
              ai_concurrency: aiConcurrency,
              deep_cap_batch_mode: useDeepCapTwoPhase,
              batch_group_key: batchGroupKey,
              batch_total_for_job: perJobResumeIds.length,
              batch_deep_cap: maxDeepPerJd,
            },
          });
          queued += 1;
          queuedRunIds.push(Number(run.id));
          lastRunId = run.id;
          if (!firstQueuedRunId) {
            firstQueuedRunId = Number(run.id);
            state.logPinnedRunId = null;
            q('selectedRunId').value = String(firstQueuedRunId);
            setTrackedBatchRunIds([firstQueuedRunId]);
            startAnalysisAutoPoll();
            await refreshRunPanels();
            await loadLogs(firstQueuedRunId);
          } else if (queued % 5 === 0) {
            setMsg('msgMatch', `Submitting analysis jobs... queued ${queued} so far.`, true);
          }
        }
      }

      if (queued === 0) throw new Error('No resumes matched selected JD tag(s).');
      if (lastRunId) {
        state.logPinnedRunId = null;
        q('selectedRunId').value = String(lastRunId);
        await loadLogs();
      }
      setTrackedBatchRunIds(queuedRunIds.slice());
      startAnalysisAutoPoll();
      setMsg('msgMatch', `Submitted ${queued} analysis job(s). Refreshing dashboard...`, true);
      await refreshAll();
      updateAnalysisQueueMessage();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    } finally {
      state.analysisSubmitting = false;
      updateStartAnalysisButtonState();
    }
  }

  async function loadLogs(runId = null) {
    const id = Number(runId || q('selectedRunId').value || 0);
    if (!id) {
      return;
    }
    try {
      const [run, logs] = await Promise.all([
        getJson(`/v1/runs/${id}`),
        getJson(`/v1/runs/${id}/logs`),
      ]);
      const el = q('runLogs');
      const prevTop = el.scrollTop;
      const prevHeight = el.scrollHeight;
      const runChanged = Number(state.lastLoadedLogRunId || 0) !== Number(id);
      const header = [
        `Run #${run.id} | ${run.job_type} | status=${run.status} | progress=${run.progress || 0}%`,
        `Step: ${run.current_step || '-'}`,
      ];
      if (run.error) header.push(`Error: ${run.error}`);
      if (run.result && Object.keys(run.result).length) {
        header.push(`Result: ${JSON.stringify(run.result)}`);
      }
      const timeline = (logs || []).map((l) => `[${l.created_at}] ${String(l.level || '').toUpperCase()} ${l.message}`);
      if (!timeline.length) {
        timeline.push('No run log lines were recorded for this run.');
      }
      el.textContent = [...header, '', ...timeline].join(String.fromCharCode(10));
      if (state.logAutoFollow || runChanged) {
        el.scrollTop = el.scrollHeight;
      } else {
        const maxTop = Math.max(0, el.scrollHeight - el.clientHeight);
        el.scrollTop = Math.min(prevTop, maxTop);
      }
      state.lastLoadedLogRunId = Number(id);
    } catch (e) {
      q('runLogs').textContent = e.message;
    }
  }

  async function loadHistoryLogs() {
    const raw = String((q('historyRunId') && q('historyRunId').value) || '').trim();
    if (!raw) return;
    state.logPinnedRunId = raw;
    if (raw.startsWith('legacy:')) {
      await loadLegacyHistoryLog(Number(raw.split(':')[1] || 0));
      return;
    }
    await loadLogs(Number(raw));
  }

  async function loadLegacyHistoryLog(legacyRunId) {
    if (!legacyRunId) {
      q('runLogs').textContent = 'No legacy run selected.';
      return;
    }
    try {
      const meta = (state.legacyRuns || []).find((r) => Number(r.id) === Number(legacyRunId)) || null;
      const results = await getJson(`/v1/runs/legacy/${legacyRunId}/results`);
      const total = results.length;
      const deep = results.filter((r) => String(r.strategy || '') === 'Deep').length;
      const std = total - deep;
      const uniqueCandidates = new Set(results.map((r) => r.candidate_name || '')).size;
      const uniqueJobs = new Set(results.map((r) => r.job_id)).size;
      const header = [
        `Legacy Run #${legacyRunId}${meta ? ` | ${meta.name}` : ''}`,
        `Created: ${meta ? (meta.created_at || '-') : '-'}`,
        `Threshold: ${meta ? (meta.threshold || 50) : 50}%`,
        '',
        `Summary: total=${total}, deep=${deep}, standard=${std}, unique_candidates=${uniqueCandidates}, unique_jobs=${uniqueJobs}`,
        '',
        'Execution logs are unavailable for legacy runs. Detailed logging exists only for background queue runs.',
      ];
      q('runLogs').textContent = header.join(String.fromCharCode(10));
    } catch (e) {
      q('runLogs').textContent = `Failed to load legacy run history: ${e.message}`;
    }
  }

  async function resumeSelectedRun() {
    try {
      const runId = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
      if (!runId) throw new Error('Select a running run first.');
      const r = await send(`/v1/runs/${runId}/resume`, 'POST', {});
      setMsg('msgMatch', r.message || `Run ${runId} resumed.`);
      await refreshRunPanels();
      await loadLogs(runId);
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  async function pauseSelectedRun() {
    try {
      state.queuePauseActionInFlight = true;
      updateRunHealthBanner();
      const runs = (state.runs || []).slice().sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
      const pausedLike = runs.filter((r) => String(r.status || '') === 'paused' || isPauseRequested(r));
      if (pausedLike.length) {
        state.pauseSettleRunId = null;
        const resp = await send('/v1/queue/resume', 'POST', {});
        setMsg('msgMatch', resp.message || 'Queue unpaused.');
        await refreshRunPanels();
        const refreshedRuns = state.runs || [];
        const runningNow = refreshedRuns
          .filter((r) => String(r.status || '') === 'running')
          .sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
        const queuedNow = refreshedRuns
          .filter((r) => String(r.status || '') === 'queued')
          .sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
        const follow = runningNow[0] || queuedNow[0] || null;
        if (follow && q('selectedRunId')) q('selectedRunId').value = String(follow.id);
        await loadLogs(follow ? Number(follow.id) : null);
        await refreshAll();
        return;
      }

      const running = runs.filter((r) => String(r.status || '') === 'running' && !isPauseRequested(r));
      const frontRun = running[0] || null;
      if (!frontRun) {
        throw new Error('No running run to pause.');
      }
      const runId = Number(frontRun.id || 0);
      state.pauseSettleRunId = runId;
      startAnalysisAutoPoll();
      const resp = await send('/v1/queue/pause', 'POST', {
        reason: 'Paused by user from web console',
      });
      setMsg('msgMatch', resp.message || `Pause requested for run ${runId}.`);
      await refreshRunPanels();
      await loadLogs(runId);
      await refreshAll();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    } finally {
      state.queuePauseActionInFlight = false;
      updateRunHealthBanner();
    }
  }

  async function cancelSelectedRun() {
    try {
      const runId = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
      if (!runId) throw new Error('Select an active run first.');
      const run = (state.runs || []).find((r) => Number(r.id) === runId) || null;
      if (!run) throw new Error(`Run ${runId} not found in active queue.`);
      const status = String(run.status || '');
      if (status !== 'queued' && status !== 'running') {
        throw new Error(`Run ${runId} is ${status} and cannot be stopped.`);
      }
      const ok = await openConfirmModal({
        title: 'Stop & Clean Run',
        message: `Stop and clean run #${runId}? This will mark it canceled and clear resumable checkpoint state.`,
        confirmText: 'Stop Run',
      });
      if (!ok) return;
      const resp = await send(`/v1/runs/${runId}/cancel`, 'POST', {
        reason: 'Stopped by user from web console',
        clean: true,
      });
      setMsg('msgMatch', resp.message || `Run ${runId} canceled.`);
      await refreshRunPanels();
      await loadLogs(runId);
      await refreshAll();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  async function skipCurrentRun() {
    try {
      const ok = await openConfirmModal({
        title: 'Skip Current Job',
        message: 'Skip the current running job and continue with the rest of the queue?',
        confirmText: 'Skip Job',
      });
      if (!ok) return;
      const resp = await send('/v1/queue/cancel-current', 'POST', {
        reason: 'Skipped current job from web console',
        clean: true,
      });
      setMsg('msgMatch', resp.message || 'Current job skipped.');
      await refreshRunPanels();
      if (resp && resp.run_id) {
        await loadLogs(Number(resp.run_id));
      } else {
        await loadLogs();
      }
      await refreshAll();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  async function cancelWholeBatch() {
    try {
      const ok = await openConfirmModal({
        title: 'Stop Whole Batch',
        message: 'Stop the whole active batch? This cancels all queued/running/paused jobs.',
        confirmText: 'Stop Batch',
      });
      if (!ok) return;
      const resp = await send('/v1/queue/cancel-all', 'POST', {
        reason: 'Stopped whole batch from web console',
        clean: true,
      });
      setMsg('msgMatch', resp.message || 'Batch stopped.');
      clearTrackedBatchRunIds();
      await refreshRunPanels();
      await loadLogs();
      await refreshAll();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  async function selectJD(id) {
    try {
      const jd = await getJson(`/v1/jobs/${id}`);
      state.selectedEditJdId = Number(jd.id);
      if (q('manageEntityType')) q('manageEntityType').value = 'job';
      if (q('manageEntitySelect')) q('manageEntitySelect').value = String(jd.id);
      q('jdEditingLabel').textContent = `Editing: ${jd.filename || ''}`;
      q('editJdTagsCsv').value = (jd.tags || []).join(', ');
      renderEditJdTagChips();
      q('editJdCriteria').value = typeof jd.criteria === 'string' ? jd.criteria : JSON.stringify(jd.criteria, null, 2);
      formatJsonEditor('editJdCriteria');
      q('jdRaw').textContent = jd.content || '';
    } catch (e) {
      setMsg('msgEditJD', e.message, false);
    }
  }

  async function selectResume(id) {
    try {
      const rs = await getJson(`/v1/resumes/${id}`);
      state.selectedEditResId = Number(rs.id);
      if (q('manageEntityType')) q('manageEntityType').value = 'resume';
      if (q('manageEntitySelect')) q('manageEntitySelect').value = String(rs.id);
      q('resEditingLabel').textContent = `Editing: ${rs.filename || ''}`;
      q('editResTagsCsv').value = (rs.tags || []).join(', ');
      renderEditResTagChips();
      q('editResProfile').value = typeof rs.profile === 'string' ? rs.profile : JSON.stringify(rs.profile, null, 2);
      formatJsonEditor('editResProfile');
      q('resRaw').textContent = rs.content || '';
    } catch (e) {
      setMsg('msgEditRes', e.message, false);
    }
  }

  async function saveJD() {
    try {
      const id = Number(state.selectedEditJdId || 0);
      if (!id) throw new Error('Select a JD first');
      if (!validateJsonEditor('editJdCriteria', 'msgEditJD')) return;
      const criteriaPayload = JSON.stringify(parseJsonText(q('editJdCriteria').value));
      await send(`/v1/jobs/${id}`, 'PUT', {
        criteria: criteriaPayload,
        tags: tagsFrom(q('editJdTagsCsv').value),
      });
      setMsg('msgEditJD', 'Saved!');
      await refreshAll();
    } catch (e) {
      setMsg('msgEditJD', e.message, false);
    }
  }

  async function deleteJD() {
    try {
      const id = Number(state.selectedEditJdId || 0);
      if (!id) throw new Error('Select a JD first');
      const r = await fetch(`/v1/jobs/${id}`, { method: 'DELETE' });
      if (!r.ok) throw new Error('Delete failed');
      setMsg('msgEditJD', 'Deleted');
      state.selectedEditJdId = null;
      q('jdEditingLabel').textContent = '';
      q('editJdCriteria').value = '';
      q('editJdTagsCsv').value = '';
      renderEditJdTagChips();
      q('jdRaw').textContent = '';
      await refreshAll();
    } catch (e) {
      setMsg('msgEditJD', e.message, false);
    }
  }

  async function saveResume() {
    try {
      const id = Number(state.selectedEditResId || 0);
      if (!id) throw new Error('Select a resume first');
      if (!validateJsonEditor('editResProfile', 'msgEditRes')) return;
      const profilePayload = JSON.stringify(parseJsonText(q('editResProfile').value));
      await send(`/v1/resumes/${id}`, 'PUT', {
        profile: profilePayload,
        tags: tagsFrom(q('editResTagsCsv').value),
      });
      setMsg('msgEditRes', 'Saved!');
      await refreshAll();
    } catch (e) {
      setMsg('msgEditRes', e.message, false);
    }
  }

  async function deleteResume() {
    try {
      const id = Number(state.selectedEditResId || 0);
      if (!id) throw new Error('Select a resume first');
      const r = await fetch(`/v1/resumes/${id}`, { method: 'DELETE' });
      if (!r.ok) throw new Error('Delete failed');
      setMsg('msgEditRes', 'Deleted');
      state.selectedEditResId = null;
      q('resEditingLabel').textContent = '';
      q('editResProfile').value = '';
      q('editResTagsCsv').value = '';
      renderEditResTagChips();
      q('resRaw').textContent = '';
      await refreshAll();
    } catch (e) {
      setMsg('msgEditRes', e.message, false);
    }
  }

  async function addTag() {
    try {
      const name = q('newTag').value.trim();
      if (!name) throw new Error('Enter tag name');
      if (state.tags.some((t) => String(t).toLowerCase() === name.toLowerCase())) {
        throw new Error('Tag already exists');
      }
      await send('/v1/tags', 'POST', { name });
      q('newTag').value = '';
      setMsg('msgTag', 'Tag added');
      await refreshAll();
    } catch (e) {
      setMsg('msgTag', e.message, false);
    }
  }

  async function renameTag() {
    try {
      const old = q('renameTagOld').value;
      const nw = q('renameTagNew').value.trim();
      if (!old || !nw) throw new Error('Select old and enter new name');
      if (old === nw) throw new Error('New name must be different');
      if (state.tags.some((t) => String(t).toLowerCase() === nw.toLowerCase())) {
        throw new Error('Tag with this name already exists');
      }
      await send('/v1/tags/rename', 'PUT', { old, new: nw });
      q('renameTagNew').value = '';
      setMsg('msgTag', 'Tag renamed');
      await refreshAll();
    } catch (e) {
      setMsg('msgTag', e.message, false);
    }
  }

  async function deleteTag() {
    try {
      const name = q('deleteTagSel').value;
      if (!name) throw new Error('Select tag');
      const usage = getTagUsage(name);
      const ok = await openConfirmModal({
        title: 'Delete Tag',
        message: `Delete tag "${name}"? It will be removed from ${usage.jd} JD(s) and ${usage.resume} resume(s).`,
        confirmText: 'Delete Tag',
      });
      if (!ok) return;
      const r = await fetch(`/v1/tags/${encodeURIComponent(name)}`, { method: 'DELETE' });
      if (!r.ok) throw new Error('Delete failed');
      setMsg('msgTag', 'Tag deleted');
      await refreshAll();
    } catch (e) {
      setMsg('msgTag', e.message, false);
    }
  }

  function renderVerifySelectors() {
    const mode = q('verifyMode').value;
    const tag = q('verifyTagFilter').value || 'All';
    let rows = [];
    if (mode === 'job') {
      rows = tag === 'All'
        ? state.jobs
        : state.jobs.filter((x) => (x.tags || []).map((t) => String(t).trim()).includes(tag));
      fillSelect('verifyItem', rows, (x) => x.filename, false);
    } else {
      rows = tag === 'All'
        ? state.resumes
        : state.resumes.filter((x) => (x.tags || []).map((t) => String(t).trim()).includes(tag));
      fillSelect('verifyItem', rows, (x) => x.filename, false);
    }
    if (!rows.length) {
      state.verifyData = null;
      state.verifyItems = [];
      q('verifyRaw').textContent = mode === 'job' ? 'No Job Descriptions available.' : 'No Resumes available.';
      q('verifyJson').textContent = '';
      q('verifyEvidence').textContent = 'Select an item to inspect evidence.';
      q('verifyClosest').textContent = 'No query yet.';
      renderVerifyEvidenceTargets();
      renderVerifyTable();
      return;
    }
    loadVerifyItem();
  }

  function parseVerifyJson(raw) {
    if (raw === null || raw === undefined) return {};
    if (typeof raw === 'string') {
      const text = raw.trim();
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (e) {
        return {};
      }
    }
    return raw;
  }

  function normalizeVerifyText(input) {
    if (!input) return '';
    let s = String(input);
    s = s.normalize('NFKC');
    s = s.replace(/\u2022/g, ' ');
    s = s.replace(/[\u2010\u2011\u2012\u2013\u2014]/g, '-');
    s = s.replace(/\s+/g, ' ');
    s = s.replace(/\s*-\s*/g, '-');
    s = s.replace(/\s*,\s*/g, ', ');
    s = s.replace(/\(\s*/g, '(');
    s = s.replace(/\s*\)/g, ')');
    return s.toLowerCase().trim();
  }

  function findEvidenceSnippet(text, query, window = 80) {
    if (!text || !query) return '';
    const normText = normalizeVerifyText(text);
    const normQuery = normalizeVerifyText(query);
    if (!normText || !normQuery) return '';
    let idx = normText.indexOf(normQuery);
    if (idx < 0) {
      const compactText = normText.replace(/[^a-z0-9]/g, '');
      const compactQuery = normQuery.replace(/[^a-z0-9]/g, '');
      idx = compactText.indexOf(compactQuery);
      if (idx < 0) {
        const tokens = normQuery.split(/\W+/).filter((t) => t.length > 3);
        const textTokens = normText.split(/\W+/).filter((t) => t.length > 3);
        if (!tokens.length || !textTokens.length) return '';
        let matched = 0;
        tokens.forEach((qt) => {
          const ok = textTokens.some((tt) => qt === tt || qt.startsWith(tt.slice(0, 4)) || tt.startsWith(qt.slice(0, 4)));
          if (ok) matched += 1;
        });
        const coverage = matched / Math.max(1, tokens.length);
        return coverage >= 0.6 ? normQuery : '';
      }
      return normQuery;
    }
    const start = Math.max(0, idx - window);
    const end = Math.min(normText.length, idx + normQuery.length + window);
    return normText.slice(start, end);
  }

  function escapeRegExp(s) {
    const special = '\\\\^$*+?.()|{}[]';
    let out = '';
    for (const ch of String(s || '')) {
      out += special.includes(ch) ? `\\${ch}` : ch;
    }
    return out;
  }

  function highlightVerifyText(text, query) {
    if (!text) return '';
    if (!query) return escapeHtml(text);
    const pattern = new RegExp(escapeRegExp(query), 'ig');
    return escapeHtml(text).replace(pattern, (m) => `<mark>${m}</mark>`);
  }

  function rankItemsByQuery(items, query) {
    const qv = String(query || '').trim().toLowerCase();
    if (!qv) return [];
    const qTokens = qv.split(/\s+/).filter(Boolean);
    const scored = [];
    items.forEach((item) => {
      if (!item || typeof item !== 'string') return;
      const lower = item.toLowerCase();
      let score = 0;
      if (lower.includes(qv)) score += 3;
      qTokens.forEach((tok) => {
        if (lower.includes(tok)) score += 1;
      });
      if (score > 0) scored.push({ score, item });
    });
    return scored.sort((a, b) => b.score - a.score).map((x) => x.item);
  }

  function extractVerifyItems(mode, data) {
    if (!data) return [];
    if (mode === 'job') {
      const criteria = parseVerifyJson(data.criteria);
      const sections = ['must_have_skills', 'nice_to_have_skills', 'education_requirements', 'domain_knowledge', 'soft_skills', 'key_responsibilities'];
      const out = [];
      sections.forEach((section) => {
        const rows = criteria && Array.isArray(criteria[section]) ? criteria[section] : [];
        rows.forEach((item) => {
          if (typeof item === 'string' && item.trim()) out.push({ section, item: item.trim() });
        });
      });
      return out;
    }
    const profile = parseVerifyJson(data.profile);
    const skills = profile && Array.isArray(profile.extracted_skills) ? profile.extracted_skills : [];
    return skills.filter((s) => typeof s === 'string' && s.trim()).map((item) => ({ section: 'extracted_skills', item: item.trim() }));
  }

  function renderVerifyEvidenceTargets() {
    const mode = q('verifyMode').value;
    const select = q('verifyEvidenceTarget');
    if (!select) return;
    const items = state.verifyItems || [];
    if (!items.length) {
      select.innerHTML = '<option value="">No items found to verify</option>';
      return;
    }
    select.innerHTML = items.map((row, idx) => {
      const label = mode === 'job' ? `${row.section}: ${row.item}` : row.item;
      return `<option value="${idx}">${escapeHtml(label)}</option>`;
    }).join('');
  }

  function renderVerifyTable() {
    const wrap = q('verifyTable');
    if (!wrap) return;
    const rawText = String((state.verifyData && state.verifyData.content) || '');
    const rows = (state.verifyItems || []).map((row) => {
      const evidence = findEvidenceSnippet(rawText, row.item);
      const status = evidence ? 'Found' : 'Not Found';
      return {
        section: row.section,
        item: row.item,
        status,
        evidence: evidence ? evidence.slice(0, 200) : '',
      };
    });
    if (!rows.length) {
      wrap.innerHTML = '<div class="caption" style="padding:10px;">No items found to verify.</div>';
      return;
    }
    wrap.innerHTML =
      '<table><thead><tr><th>Section</th><th>Item</th><th>Status</th><th>Evidence</th></tr></thead><tbody>' +
      rows.map((r) => `<tr><td>${escapeHtml(r.section)}</td><td>${escapeHtml(r.item)}</td><td>${escapeHtml(r.status)}</td><td>${escapeHtml(r.evidence)}</td></tr>`).join('') +
      '</tbody></table>';
  }

  async function loadVerifyItem() {
    const mode = q('verifyMode').value;
    const id = Number(q('verifyItem').value);
    if (!id) {
      state.verifyData = null;
      state.verifyItems = [];
      q('verifyRaw').textContent = '';
      q('verifyJson').textContent = '';
      q('verifyEvidence').textContent = 'Select an item to inspect evidence.';
      q('verifyClosest').textContent = 'No query yet.';
      renderVerifyEvidenceTargets();
      renderVerifyTable();
      return;
    }
    try {
      const d = mode === 'job' ? await getJson(`/v1/jobs/${id}`) : await getJson(`/v1/resumes/${id}`);
      state.verifyData = d;
      state.verifyItems = extractVerifyItems(mode, d);
      q('verifyRaw').textContent = d.content || '';
      const parsed = mode === 'job' ? d.criteria : d.profile;
      q('verifyJson').textContent = typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2);
      q('verifyEvidence').textContent = 'Select an item to inspect evidence.';
      q('verifyClosest').textContent = 'No query yet.';
      renderVerifyEvidenceTargets();
      renderVerifyTable();
    } catch (e) {
      q('verifyRaw').textContent = e.message;
      q('verifyJson').textContent = '';
      q('verifyEvidence').textContent = '';
      q('verifyClosest').textContent = '';
      state.verifyData = null;
      state.verifyItems = [];
      renderVerifyEvidenceTargets();
      renderVerifyTable();
    }
  }

  function runEvidenceCheck() {
    const idx = Number(q('verifyEvidenceTarget').value);
    const row = (state.verifyItems || [])[idx];
    if (!row) {
      q('verifyEvidence').textContent = 'No item selected.';
      return;
    }
    const text = String((state.verifyData && state.verifyData.content) || '');
    const evidence = findEvidenceSnippet(text, row.item);
    if (!evidence) {
      q('verifyEvidence').textContent = 'No exact evidence found in raw text.';
      return;
    }
    q('verifyEvidence').innerHTML = highlightVerifyText(evidence, row.item);
  }

  function runVerifySimilarity() {
    const query = String(q('verifyQuery').value || '').trim();
    if (!query) {
      q('verifyClosest').textContent = 'Enter a sentence or phrase.';
      return;
    }
    const items = (state.verifyItems || []).map((x) => x.item);
    const ranked = rankItemsByQuery(items, query);
    if (!ranked.length) {
      q('verifyClosest').textContent = 'No similar items found.';
      return;
    }
    q('verifyClosest').innerHTML = `<ul class="verify-list">${ranked.slice(0, 10).map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
  }

  async function runDebugHealthCheck() {
    try {
      const r = await getJson('/health');
      debugLog(`/health ok: ${JSON.stringify(r)}`);
    } catch (e) {
      debugLog(`/health failed: ${e.message}`, 'error');
    }
  }

  function copyDebugLog() {
    const payload = debugLines.join('\\n') || 'No debug log entries.';
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(payload)
        .then(() => debugLog('Debug log copied to clipboard.'))
        .catch((e) => debugLog(`Clipboard copy failed: ${e.message}`, 'error'));
      return;
    }
    debugLog('Clipboard API unavailable; copy manually from Debug Tools panel.', 'warn');
  }

  async function boot() {
    try {
      await refreshAll();
      toggleResultsMode();
      switchManage('upload');
      const persistedBatchIds = loadPersistedBatchRunIds();
      if (persistedBatchIds.length) {
        setTrackedBatchRunIds(persistedBatchIds);
        updateAnalysisQueueMessage();
      }
      await loadSettings();
      const hasTrackedActive = (state.analysisQueuedRunIds || []).some((id) =>
        (state.runs || []).some((r) => Number(r.id) === Number(id) && (r.status === 'queued' || r.status === 'running'))
      );
      if (!isQueuePausedByRuns(state.runs || []) && (hasTrackedActive || (state.runs || []).some((r) => r.status === 'queued' || r.status === 'running'))) {
        startAnalysisAutoPoll();
      }
      renderVerifySelectors();
      const logEl = q('runLogs');
      if (logEl && !logEl.dataset.boundScroll) {
        logEl.addEventListener('scroll', () => {
          const delta = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight;
          state.logAutoFollow = delta <= 24;
        });
        logEl.dataset.boundScroll = '1';
      }
      debugLog('Boot complete.');
    } catch (e) {
      debugLog(`Boot failed: ${e.message}`, 'error');
      console.error(e);
    }
  }

  boot();
  setInterval(async () => {
    try {
      await pollRunActivity();
    } catch (e) {
      console.error(e);
    }
  }, 3000);

  document.addEventListener('click', (e) => {
    const wrap = q('settingsBtn');
    const menu = q('settingsMenu');
    if (!wrap || !menu) return;
    if (wrap.contains(e.target) || menu.contains(e.target)) return;
    closeSettingsMenu();
  });
</script>
</body>
    </html>
    """
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
