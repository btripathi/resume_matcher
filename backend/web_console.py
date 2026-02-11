from fastapi.responses import HTMLResponse


def render_console() -> HTMLResponse:
    html = """
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
    .check-inline { display: flex; align-items: center; gap: 8px; }

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
    .export-block {
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #f8fbff;
      padding: 12px;
      margin: 8px 0 14px;
    }
    .export-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 8px;
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
    #legacyMatchDetail {
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
      .grid2, .grid3, .row2, .row3, .metrics3, .metrics5 { grid-template-columns: 1fr; }
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
      <div class="subtabs">
        <button class="subtab active" id="sub-results-simple" onclick="switchResults('simple')">📌 Simple JD View</button>
        <button class="subtab" id="sub-results-run" onclick="switchResults('run')">📊 Run-Based Results</button>
      </div>

      <div class="subpanel active" id="panel-results-simple">
        <div class="section">
          <label style="font-size:18px; display:block; margin-bottom:6px;">Select Job Description:</label>
          <select id="simpleJobSelect" onchange="renderSimpleResults()"></select>
          <label class="caption row check-inline"><input id="simpleFilterByJdTags" type="checkbox" checked onchange="renderSimpleResults()" /> Show only resumes matching selected JD tag(s)</label>
          <div class="caption" id="simpleResultScope">Showing all saved matches for selected JD.</div>
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
      </div>

      <div class="subpanel run-results-panel" id="panel-results-run">
        <div class="section">
          <label style="font-size:18px; display:block; margin-bottom:6px;">Select Run Batch:</label>
          <select id="legacyRunSelect" onchange="loadLegacyRunResults()"></select>
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
            <div></div>
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
        <div class="export-block">
          <div style="font-size:14px; font-weight:600; color:#334155;">Export Run Results</div>
          <div class="caption">Download selected run data for sharing or audits.</div>
          <div class="export-actions">
            <button class="secondary" onclick="downloadLegacyCsv()">📥 Download CSV</button>
            <button class="secondary" onclick="downloadLegacyJson()">🧾 Download JSON</button>
          </div>
        </div>
        <div class="section">
          <h3 id="legacyDeepHeading">✨ Deep Matches for Selected Run</h3>
          <div class="table-wrap" id="legacyDeepTable"></div>
        </div>
        <div class="section">
          <h3>🧠 Standard Matches (Pass 1 Only)</h3>
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
          <label class="caption check-inline" style="margin-top:24px;">
            <input id="analysisAutoTagMatch" type="checkbox" checked onchange="onAnalysisSelectionChange()" />
            🎯 Auto-match based on JD Tags
          </label>
        </div>
      </div>
      <div class="caption section">
        <div id="selectedCountJd">Selected JDs: 0 / 0</div>
        <div id="selectedCountRes">Selected Resumes: 0 / 0</div>
      </div>

      <div class="card section">
        <h3>⚙️ Smart Match Configuration</h3>
        <div class="row2">
          <input id="runName" placeholder="Run Name" />
          <div>
            <label class="caption" style="display:block; margin-bottom:4px;">Deep Match Threshold (%)</label>
            <div class="row2" style="grid-template-columns: 1fr 60px; align-items:center;">
              <input id="threshold" type="range" min="0" max="100" value="50" oninput="q('thresholdValue').textContent=this.value" />
              <span id="thresholdValue" style="font-weight:700; text-align:right;">50</span>
            </div>
          </div>
        </div>
        <label class="caption row check-inline"><input id="autoDeep" type="checkbox" /> ✨ Auto-Upgrade to Deep Match</label>
        <div class="row3 row">
          <label class="caption check-inline"><input id="forceRerunPass1" type="checkbox" /> Force Re-run Pass 1 (Standard Match)</label>
          <label class="caption check-inline"><input id="forceRerunDeep" type="checkbox" onchange="syncAnalysisDeepForce()" /> Force Re-run Deep Scan</label>
          <div></div>
        </div>
        <button class="primary row" onclick="queueScoreMatch()">🚀 START ANALYSIS</button>
        <div class="msg" id="msgMatch"></div>
      </div>

      <div class="card">
        <h3>Live Run Logs</h3>
        <div class="caption" id="runCounts">Running: 0 | Queued: 0 | Completed: 0 | Failed: 0</div>
        <div class="run-stuck-alert" id="runStuckAlert"></div>
        <div class="run-health" id="runHealthBox">
          <div class="run-health-title">Selected Run Status</div>
          <div class="run-health-meta" id="runHealthMeta">No active run selected.</div>
          <div class="run-health-actions">
            <button class="danger" id="resumeRunBtn" style="display:none;" onclick="resumeSelectedRun()">Resume Stuck Run</button>
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
          <summary>History Runs (Completed / Failed)</summary>
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
        <button class="subtab active" id="sub-manage-jd" onclick="switchManage('jd')">📂 Job Descriptions</button>
        <button class="subtab" id="sub-manage-res" onclick="switchManage('res')">📄 Candidate Resumes</button>
        <button class="subtab" id="sub-manage-tags" onclick="switchManage('tags')">🏷️ Tag Manager</button>
        <button class="subtab" id="sub-manage-verify" onclick="switchManage('verify')">✅ Data Verification</button>
      </div>

      <div class="subpanel active" id="panel-manage-jd">
        <details class="expander">
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

        <details class="expander">
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

        <div class="card">
          <h3>Manage JDs</h3>
          <div class="caption" id="jdCount">Total Job Descriptions: 0</div>
          <div class="table-wrap row" id="jobsTable"></div>
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
        <details class="expander">
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

        <details class="expander">
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

        <div class="card">
          <h3>Manage Resumes</h3>
          <div class="row2">
            <select id="resTagFilter" onchange="renderResumes()"></select>
            <div class="caption" id="resCount">Total Resumes: 0</div>
          </div>
          <div class="table-wrap row" id="resumesTable"></div>
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
      </div>

      <div class="subpanel" id="panel-manage-verify">
        <div class="card">
          <h3>Data Verification</h3>
          <div class="caption">Compare extracted text with JSON to verify accuracy.</div>
          <div class="row3 row">
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

<script>
  const state = {
    jobs: [], resumes: [], tags: [], matches: [], runs: [], legacyRuns: [], legacyRunResults: [], verifyData: null,
    verifyItems: [],
    selectedLegacyRunId: null,
    selectedLegacyMatchId: null,
    lastAutoRunName: null,
    analysisQueuedRunIds: [],
    analysisAutoPollEnabled: false,
    logPinnedRunId: null,
    settings: null,
    selectedEditJdId: null,
    selectedEditResId: null,
  };

  const q = (id) => document.getElementById(id);
  const tagsFrom = (s) => String(s || '').split(',').map(x => x.trim()).filter(Boolean);
  const escapeHtml = (s) => String(s || '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const DEBUG_LOG_LIMIT = 300;
  const debugLines = [];

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

  function addJdUploadTag() {
    const tag = String((q('jdTagAssign').value || '')).trim();
    if (!tag) return;
    const tags = tagsFrom(q('jdTagsCsv').value);
    if (!tags.includes(tag)) tags.push(tag);
    q('jdTagsCsv').value = tags.join(', ');
    renderJdUploadTagChips();
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
    info.textContent = `${files.length} file(s) selected:\\n${names.join('\\n')}`;
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

  function updateRunStatusBars() {
    const runs = state.runs || [];
    const active = runs
      .filter((r) => r.status === 'queued' || r.status === 'running')
      .sort((a, b) => {
        const pa = a.status === 'running' ? 0 : 1;
        const pb = b.status === 'running' ? 0 : 1;
        if (pa !== pb) return pa - pb;
        return Number(b.id || 0) - Number(a.id || 0);
      });

    const selectedRunId = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
    const selected = runs.find((r) => Number(r.id) === selectedRunId) || active[0] || null;
    const jobPct = selected ? Math.max(0, Math.min(100, Number(selected.progress || 0))) : 0;
    const jobLabel = selected ? `Current Job • #${selected.id} • ${selected.status || 'unknown'}` : 'Current Job • idle';
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
      const running = rows.filter((r) => r.status === 'running').length;
      const queuedKnown = rows.filter((r) => r.status === 'queued').length;
      const queuedUnknown = Math.max(0, total - known);
      const queued = queuedKnown + queuedUnknown;
      const done = completed + failed;
      const pct = total ? Math.round((done / total) * 100) : 0;
      const failPart = failed ? `, ${failed} failed` : '';
      const runPart = running ? `, ${running} running` : '';
      const queuePart = queued ? `, ${queued} queued` : '';

      if (q('batchProgressLabel')) q('batchProgressLabel').textContent = `Batch Progress • ${total} job(s)`;
      if (q('batchProgressMeta')) q('batchProgressMeta').textContent = `${completed}/${total} complete${failPart}${runPart}${queuePart}`;
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
    if (!box || !meta || !btn) return;
    const selectedRunId = Number((q('selectedRunId') && q('selectedRunId').value) || 0);
    const run = (state.runs || []).find((r) => Number(r.id) === selectedRunId) || null;
    btn.style.display = 'none';
    box.classList.remove('stuck');
    if (!run) {
      meta.textContent = 'No active run selected.';
      return;
    }
    const status = String(run.status || 'unknown');
    const step = String(run.current_step || '-');
    const pct = Number(run.progress || 0);
    const stuck = !!run.is_stuck;
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
      meta.textContent = `Run #${run.id} appears stuck (${sec}s without progress). Last step: ${step}.`;
      box.classList.add('stuck');
      btn.style.display = 'inline-flex';
      return;
    }
    if (status === 'running' && lagSec >= 45) {
      meta.textContent = `Run #${run.id} is active at ${pct}% • waiting on model response for ~${lagSec}s • step: ${step}`;
      return;
    }
    meta.textContent = `Run #${run.id} is ${status} at ${pct}% • step: ${step}`;
  }

  function updateAnalysisQueueMessage() {
    const ids = (state.analysisQueuedRunIds || []).map((x) => Number(x)).filter(Boolean);
    if (!ids.length) {
      updateRunStatusBars();
      return;
    }

    const rows = ids
      .map((id) => state.runs.find((r) => Number(r.id) === id))
      .filter(Boolean);
    if (!rows.length) {
      updateRunStatusBars();
      return;
    }

    const completed = rows.filter((r) => r.status === 'completed').length;
    const running = rows.filter((r) => r.status === 'running').length;
    const queued = rows.filter((r) => r.status === 'queued').length;
    const failed = rows.filter((r) => r.status === 'failed').length;

    const idPreview = ids.length <= 6 ? ids.join(', ') : `${ids.slice(0, 6).join(', ')}, ...`;
    const total = ids.length;
    if (completed === total && failed === 0) {
      setMsg('msgMatch', '', true);
      updateRunStatusBars();
      return;
    }

    const text = `Submitted ${total} analysis job(s): completed ${completed}, running ${running}, queued ${queued}, failed ${failed}. Runs #${idPreview}.`;
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
    if (q('historyRunId') && id) q('historyRunId').value = '';
    await loadLogs(id || null);
  }

  async function onHistoryRunSelection() {
    const id = Number((q('historyRunId') && q('historyRunId').value) || 0);
    state.logPinnedRunId = id || null;
    await loadLogs(id || null);
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
    q('setOcrEnabled').checked = !!s.ocr_enabled;
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
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  async function saveSettingsConfig() {
    try {
      await send('/v1/settings/runtime', 'PUT', {
        lm_base_url: q('setLmUrl').value.trim(),
        lm_api_key: q('setApiKey').value.trim(),
        ocr_enabled: q('setOcrEnabled').checked,
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
      if (!window.confirm('Reset DB will delete jobs, resumes, matches, and runs. Continue?')) return;
      const r = await send('/v1/settings/reset-db', 'POST', {});
      await refreshAll();
      await loadSettings();
      setSettingsMsg(r.message || 'Database reset complete.');
    } catch (e) {
      setSettingsMsg(e.message, false);
    }
  }

  function switchManage(name) {
    ['jd', 'res', 'tags', 'verify'].forEach((t) => {
      q(`sub-manage-${t}`).classList.toggle('active', t === name);
      q(`panel-manage-${t}`).classList.toggle('active', t === name);
    });
  }

  function switchResults(name) {
    ['simple', 'run'].forEach((t) => {
      q(`sub-results-${t}`).classList.toggle('active', t === name);
      q(`panel-results-${t}`).classList.toggle('active', t === name);
    });
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
    q('jdCount').textContent = `Total Job Descriptions: ${state.jobs.length}`;
    q('jobsTable').innerHTML = `<table><thead><tr><th>Filename</th><th>Tags</th><th>Upload Date</th></tr></thead><tbody>` +
      state.jobs.map((j) => `<tr style="cursor:pointer" onclick="selectJD(${j.id})"><td>${j.filename}</td><td>${(j.tags || []).join(', ')}</td><td>${j.upload_date || ''}</td></tr>`).join('') +
      `</tbody></table>`;
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
    q('resCount').textContent = `Total Resumes: ${state.resumes.length} | Filtered Resumes: ${rows.length}`;
    q('resumesTable').innerHTML = `<table><thead><tr><th>Filename</th><th>Tags</th><th>Upload Date</th></tr></thead><tbody>` +
      rows.map((r) => `<tr style="cursor:pointer" onclick="selectResume(${r.id})"><td>${r.filename}</td><td>${(r.tags || []).join(', ')}</td><td>${r.upload_date || ''}</td></tr>`).join('') +
      `</tbody></table>`;
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
    let defaultName = `Run ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    if (selectedJob && selectedJob !== '__all__') {
      const job = state.jobs.find((j) => String(j.id) === String(selectedJob));
      if (job && job.filename) {
        defaultName = `Run: ${String(job.filename).replace(/\\.[^/.]+$/, '')}`;
      }
    } else {
      defaultName = `Batch Run: ${state.jobs.length} Jobs`;
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

  function onAnalysisSelectionChange() {
    const jdSel = q('matchJobSelect');
    const rsSel = q('matchResumeSelect');
    if (jdSel) {
      const selectedJob = jdSel.value;
      let defaultName = `Run ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      if (selectedJob && selectedJob !== '__all__') {
        const job = state.jobs.find((j) => String(j.id) === String(selectedJob));
        if (job && job.filename) defaultName = `Run: ${String(job.filename).replace(/\\.[^/.]+$/, '')}`;
      } else {
        defaultName = `Batch Run: ${state.jobs.length} Jobs`;
      }
      const runNameInput = q('runName');
      const currentValue = (runNameInput.value || '').trim();
      if (!currentValue || currentValue === state.lastAutoRunName) runNameInput.value = defaultName;
      state.lastAutoRunName = defaultName;
    }
    const jdCount = jdSel && jdSel.value === '__all__' ? state.jobs.length : (jdSel && jdSel.value ? 1 : 0);
    const resOptions = rsSel ? Array.from(rsSel.options).filter((o) => o.value !== '__all__').length : 0;
    const rsCount = rsSel && rsSel.value === '__all__' ? resOptions : (rsSel && rsSel.value ? 1 : 0);
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
    renderResUploadTagChips();

    const prevResEdit = q('editResTagSelect').value;
    q('editResTagSelect').innerHTML = '<option value="">Select tag</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
    if (prevResEdit && Array.from(q('editResTagSelect').options).some((o) => o.value === prevResEdit)) {
      q('editResTagSelect').value = prevResEdit;
    }

    q('verifyTagFilter').innerHTML = '<option value="All">All Tags</option>' + state.tags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
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
      .filter((r) => r.status === 'queued' || r.status === 'running')
      .sort((a, b) => {
        const pa = a.status === 'running' ? 0 : 1;
        const pb = b.status === 'running' ? 0 : 1;
        if (pa !== pb) return pa - pb;
        return Number(b.id || 0) - Number(a.id || 0);
      });
    const history = runs.filter((r) => r.status === 'completed' || r.status === 'failed');

    const activeSel = q('selectedRunId');
    const historySel = q('historyRunId');
    if (!activeSel || !historySel) return;

    const prevActive = activeSel.value;
    const prevHistory = historySel.value;

    const fmt = (r) => {
      const stuckTag = r.is_stuck ? ' | STUCK' : '';
      return `#${r.id} | ${r.job_type} | ${r.status}${stuckTag} | ${r.progress || 0}% | ${r.current_step || '-'}`;
    };

    if (active.length) {
      activeSel.innerHTML = active.map((r) => `<option value="${r.id}">${fmt(r)}</option>`).join('');
      const stuckActive = active
        .filter((r) => r.status === 'running' && r.is_stuck)
        .sort((a, b) => Number(b.stuck_seconds || 0) - Number(a.stuck_seconds || 0));
      if (prevActive && active.some((r) => String(r.id) === String(prevActive))) {
        activeSel.value = String(prevActive);
      } else if (state.logPinnedRunId && active.some((r) => Number(r.id) === Number(state.logPinnedRunId))) {
        activeSel.value = String(state.logPinnedRunId);
      } else {
        // Focus stuck run first so blocked work is immediately visible.
        activeSel.value = String((stuckActive[0] || active[0]).id);
      }
    } else {
      activeSel.innerHTML = '<option value="">No active runs</option>';
    }

    if (history.length) {
      historySel.innerHTML = '<option value="">Select completed/failed run</option>' +
        history.map((r) => `<option value="${r.id}">${fmt(r)}</option>`).join('');
      if (state.logPinnedRunId && history.some((r) => Number(r.id) === Number(state.logPinnedRunId))) {
        historySel.value = String(state.logPinnedRunId);
      } else if (prevHistory && history.some((r) => String(r.id) === String(prevHistory))) {
        historySel.value = String(prevHistory);
      }
    } else {
      historySel.innerHTML = '<option value="">No completed/failed runs</option>';
    }

    const running = runs.filter((r) => r.status === 'running').length;
    const queued = runs.filter((r) => r.status === 'queued').length;
    const completed = runs.filter((r) => r.status === 'completed').length;
    const failed = runs.filter((r) => r.status === 'failed').length;
    const stuckRuns = runs.filter((r) => r.status === 'running' && r.is_stuck);
    const stuck = stuckRuns.length;
    q('runCounts').textContent = `Running: ${running} | Queued: ${queued} | Completed: ${completed} | Failed: ${failed} | Stuck: ${stuck}`;
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
  }

  function renderSimpleResults() {
    const selectedJob = Number(q('simpleJobSelect').value);
    const onlyTagged = !!(q('simpleFilterByJdTags') && q('simpleFilterByJdTags').checked);
    const allRows = state.matches.filter((m) => !selectedJob || Number(m.job_id) === selectedJob);
    let rows = allRows;
    let excludedByTag = 0;
    if (selectedJob && onlyTagged) {
      const job = state.jobs.find((j) => Number(j.id) === selectedJob);
      const jdTags = (job && job.tags) ? job.tags.map((t) => String(t).trim().toLowerCase()).filter(Boolean) : [];
      if (jdTags.length) {
        rows = allRows.filter((m) => {
          const rs = state.resumes.find((r) => Number(r.id) === Number(m.resume_id));
          const rsTags = (rs && rs.tags) ? rs.tags.map((t) => String(t).trim().toLowerCase()).filter(Boolean) : [];
          return jdTags.some((t) => rsTags.includes(t));
        });
        excludedByTag = Math.max(0, allRows.length - rows.length);
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
      } else if (onlyTagged && excludedByTag > 0) {
        q('simpleResultScope').textContent = `Showing tag-compatible matches for selected JD. ${excludedByTag} historical match(es) hidden by tag filter.`;
      } else if (onlyTagged) {
        q('simpleResultScope').textContent = 'Showing tag-compatible matches for selected JD.';
      } else {
        q('simpleResultScope').textContent = 'Showing all saved matches for selected JD (including historical).';
      }
    }

    const renderTable = (arr) => `<table><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th></tr></thead><tbody>` +
      arr.map((r) => `<tr><td>${r.candidate_name || ''}</td><td><b>${r.match_score}%</b></td><td>${decisionBadge(r.decision)}</td><td>${r.reasoning || ''}</td></tr>`).join('') +
      `</tbody></table>`;

    q('simpleDeepTable').innerHTML = renderTable(deep);
    q('simpleStdTable').innerHTML = renderTable(std);
  }

  function renderLegacyRunResults() {
    const rows = state.legacyRunResults || [];
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
    q('runUniqueJobs').textContent = String(new Set(rows.map((r) => r.job_name || '')).size);

    const tableHTML = (arr) => `<table><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th></tr></thead><tbody>` +
      arr.map((r) => `<tr style="cursor:pointer" onclick="showLegacyMatch(${r.id})"><td>${r.candidate_name || ''}</td><td><b>${r.match_score}%</b>${r.standard_score !== null && r.standard_score !== undefined ? `<span class="score-sub">Pass 1: ${r.standard_score}%</span>` : ''}</td><td>${decisionBadge(r.decision || '')}</td><td>${r.reasoning || ''}</td></tr>`).join('') +
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
      runName: (q('legacyRerunName').value || '').trim() || null,
    };
  }

  async function queueLegacyBatchRerun() {
    try {
      const rows = state.legacyRunResults || [];
      if (!rows.length) throw new Error('No results in selected run batch.');
      const cfg = getLegacyRerunConfig();
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
            run_name: cfg.runName,
            force_rerun_pass1: cfg.forcePass1,
            force_rerun_deep: cfg.forceDeep,
          },
        });
        queued += 1;
        runIds.push(Number(run.id));
      }
      if (queued === 0) throw new Error('No rerun tasks were queued.');
      state.analysisQueuedRunIds = runIds.slice();
      startAnalysisAutoPoll();
      await refreshRunPanels();
      setMsg('msgLegacyRerun', `Queued batch rerun: ${queued} task(s), run #${runIds.join(', ')}.`);
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
        },
      });
      q('selectedRunId').value = String(run.id);
      state.analysisQueuedRunIds = [Number(run.id)];
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
    updateAnalysisQueueMessage();
  }

  function runSignature(rows) {
    return (rows || [])
      .map((r) => `${r.id}:${r.status}:${r.progress || 0}:${r.current_step || ''}`)
      .join('|');
  }

  async function pollRunActivity() {
    if (!state.analysisAutoPollEnabled) return;
    const analysisActive = q('panel-analysis').classList.contains('active');
    if (!analysisActive) return;

    const previousRuns = state.runs || [];
    const hadActive = previousRuns.some((r) => r.status === 'queued' || r.status === 'running');
    const previousById = new Map(previousRuns.map((r) => [Number(r.id), r]));

    const runs = await getJson('/v1/runs');
    const hasActive = runs.some((r) => r.status === 'queued' || r.status === 'running');
    const runChanged = runSignature(previousRuns) !== runSignature(runs);

    state.runs = runs;
    renderRuns();
    updateAnalysisQueueMessage();

    const pinnedRunId = getPinnedRunId();
    if (pinnedRunId) {
      await loadLogs(pinnedRunId);
    } else {
      const selectedRunId = Number(q('selectedRunId').value || 0);
      if (selectedRunId) await loadLogs(selectedRunId);
    }

    if (!runChanged) return;

    // Refresh heavy datasets only when a run transitions from active -> terminal.
    const transitioned = runs.filter((r) => {
      const prev = previousById.get(Number(r.id));
      if (!prev) return false;
      const prevActive = prev.status === 'queued' || prev.status === 'running';
      const nowTerminal = r.status === 'completed' || r.status === 'failed';
      return prevActive && nowTerminal;
    });

    if (!transitioned.length) return;

    const affectsData = transitioned.some((r) =>
      r.job_type === 'ingest_job' || r.job_type === 'ingest_resume' || r.job_type === 'score_match'
    );
    if (affectsData || hadActive !== hasActive) {
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
    const activeRunId = Number(q('selectedRunId').value || 0);
    if (activeRunId) return loadLogs(activeRunId);
    const historyRunId = Number(q('historyRunId').value || 0);
    if (historyRunId) return loadLogs(historyRunId);
  }

  async function loadLegacyRunResults(preserveSelection = false) {
    const runId = Number(q('legacyRunSelect').value);
    state.selectedLegacyRunId = runId || null;
    if (!runId) {
      state.legacyRunResults = [];
      state.selectedLegacyMatchId = null;
      renderLegacyRunResults();
      q('legacyRunCaption').textContent = '';
      q('legacyMatchDetail').textContent = 'Select a row to inspect.';
      q('legacyDeepHeading').textContent = '✨ Deep Matches for Selected Run';
      q('legacySingleRerunMatch').innerHTML = '<option value="">No candidates in selected run</option>';
      setMsg('msgLegacyRerun', '');
      return;
    }
    state.legacyRunResults = await getJson(`/v1/runs/legacy/${runId}/results`);
    const meta = state.legacyRuns.find((r) => Number(r.id) === runId);
    q('legacyRunCaption').textContent = meta ? `Results showing against Deep Match Threshold of ${meta.threshold}% used in this run.` : '';
    q('legacyDeepHeading').textContent = meta ? `✨ Deep Matches for ${meta.name}` : '✨ Deep Matches for Selected Run';
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
    setMsg('msgLegacyRerun', `JSON exported (${rows.length} rows).`);
  }

  async function showLegacyMatch(matchId, preserve = false) {
    try {
      state.selectedLegacyMatchId = Number(matchId);
      if (q('legacySingleRerunMatch')) q('legacySingleRerunMatch').value = String(matchId);
      const d = await getJson(`/v1/matches/${matchId}`);
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

      q('legacyMatchDetail').innerHTML = `
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
    } catch (e) {
      if (!preserve) q('legacyMatchDetail').textContent = e.message;
    }
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
      state.analysisQueuedRunIds = runIds.slice();
      startAnalysisAutoPoll();
      await refreshAll();
    } catch (e) {
      setMsg('msgJD', e.message, false);
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
      state.analysisQueuedRunIds = runIds.slice();
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
      state.analysisQueuedRunIds = runIds.slice();
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
      state.analysisQueuedRunIds = runIds.slice();
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
      state.analysisQueuedRunIds = runIds.slice();
      startAnalysisAutoPoll();
      setMsg('msgRes', `Queued ${runIds.length} resume import run(s): #${runIds.join(', ')}`);
      await refreshAll();
    } catch (e) {
      setMsg('msgRes', e.message, false);
    }
  }

  async function queueScoreMatch() {
    try {
      const jobSel = q('matchJobSelect').value;
      const resSel = q('matchResumeSelect').value;
      const autoTag = q('analysisAutoTagMatch') && q('analysisAutoTagMatch').checked;

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

      let queued = 0;
      const queuedRunIds = [];
      let lastRunId = null;
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

        for (const resume_id of perJobResumeIds) {
          const run = await send('/v1/runs', 'POST', {
            job_type: 'score_match',
            payload: {
              job_id,
              resume_id,
              threshold,
              auto_deep: autoDeep,
              run_name: runName,
              force_rerun_pass1: forceRerunPass1,
              force_rerun_deep: forceRerunDeep,
            },
          });
          queued += 1;
          queuedRunIds.push(Number(run.id));
          lastRunId = run.id;
        }
      }

      if (queued === 0) throw new Error('No resumes matched selected JD tag(s).');
      if (lastRunId) {
        q('selectedRunId').value = String(lastRunId);
        await loadLogs();
      }
      state.analysisQueuedRunIds = queuedRunIds.slice();
      startAnalysisAutoPoll();
      await refreshAll();
      updateAnalysisQueueMessage();
    } catch (e) {
      setMsg('msgMatch', e.message, false);
    }
  }

  async function loadLogs(runId = null) {
    const id = Number(runId || q('selectedRunId').value || 0);
    if (!id) {
      q('runLogs').textContent = 'No active run selected.';
      return;
    }
    try {
      const logs = await getJson(`/v1/runs/${id}/logs`);
      const el = q('runLogs');
      el.textContent = logs.map((l) => `[${l.created_at}] ${String(l.level || '').toUpperCase()} ${l.message}`).join(String.fromCharCode(10));
      el.scrollTop = el.scrollHeight;
    } catch (e) {
      q('runLogs').textContent = e.message;
    }
  }

  async function loadHistoryLogs() {
    const id = Number(q('historyRunId').value || 0);
    if (!id) return;
    state.logPinnedRunId = id;
    await loadLogs(id);
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

  async function selectJD(id) {
    try {
      const jd = await getJson(`/v1/jobs/${id}`);
      state.selectedEditJdId = Number(jd.id);
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
      const ok = confirm(`Delete tag "${name}"?\n\nIt will be removed from ${usage.jd} JD(s) and ${usage.resume} resume(s).`);
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
      await loadSettings();
      if ((state.runs || []).some((r) => r.status === 'queued' || r.status === 'running')) {
        startAnalysisAutoPoll();
      }
      renderVerifySelectors();
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
