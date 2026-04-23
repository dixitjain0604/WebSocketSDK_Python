#!/usr/bin/env python3
"""
Generate the WebSocket SDK Device Management System — User Manual PDF.
Run:  python3 generate_manual.py
Output: UserManual.pdf
"""

import os, sys, base64, io
from weasyprint import HTML, CSS

# ── tiny helper: build a fake browser-style screenshot as an HTML table ──────

def screen(title, rows, buttons=None, badge=None, note=None):
    """Return HTML for a mocked UI screenshot panel."""
    button_html = ""
    if buttons:
        button_html = "<div style='margin-top:10px;'>" + "".join(
            f"<span style='display:inline-block;background:{c};color:#fff;padding:4px 14px;"
            f"border-radius:4px;font-size:11px;margin-right:6px;font-family:sans-serif;'>{b}</span>"
            for b, c in buttons
        ) + "</div>"

    badge_html = ""
    if badge:
        badge_html = f"<span style='float:right;background:#198754;color:#fff;padding:2px 8px;border-radius:10px;font-size:10px;'>{badge}</span>"

    row_html = ""
    for row in rows:
        if row == "---":
            row_html += "<tr><td colspan='2'><hr style='margin:4px 0;border-color:#dee2e6;'></td></tr>"
            continue
        if isinstance(row, str):
            row_html += f"<tr><td colspan='2' style='color:#6c757d;font-size:10px;padding:3px 8px;'>{row}</td></tr>"
            continue
        k, v = row
        row_html += (
            f"<tr>"
            f"<td style='color:#495057;font-weight:600;padding:4px 8px 4px 12px;white-space:nowrap;"
            f"font-size:11px;width:38%;border-right:1px solid #dee2e6;'>{k}</td>"
            f"<td style='padding:4px 12px;font-size:11px;color:#212529;'>{v}</td>"
            f"</tr>"
        )

    note_html = ""
    if note:
        note_html = f"<div style='background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:5px 10px;margin-top:8px;font-size:10px;color:#856404;'>{note}</div>"

    return f"""
<div class="screenshot">
  <div class="screen-title">{badge_html}{title}</div>
  <table style="width:100%;border-collapse:collapse;">{row_html}</table>
  {button_html}
  {note_html}
</div>"""


def nav_bar(*items):
    links = " &nbsp;|&nbsp; ".join(
        f"<span style='color:#0d6efd;font-size:11px;'>{i}</span>" for i in items
    )
    return f"""<div class="screen-nav">{links}</div>"""


def table_screen(title, headers, data_rows, note=None):
    th = "".join(f"<th>{h}</th>" for h in headers)
    rows_html = ""
    for dr in data_rows:
        td = "".join(f"<td>{c}</td>" for c in dr)
        rows_html += f"<tr>{td}</tr>"
    note_html = f"<div style='background:#d1ecf1;border:1px solid #bee5eb;border-radius:4px;padding:5px 10px;margin-top:8px;font-size:10px;color:#0c5460;'>{note}</div>" if note else ""
    return f"""
<div class="screenshot">
  <div class="screen-title">{title}</div>
  <table class="tbl"><thead><tr>{th}</tr></thead><tbody>{rows_html}</tbody></table>
  {note_html}
</div>"""


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS_STR = """
@page {
  size: A4;
  margin: 18mm 16mm 18mm 16mm;
  @top-center {
    content: "Device Management System — User Manual";
    font-size: 8pt;
    color: #6c757d;
    font-family: Arial, sans-serif;
  }
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 8pt;
    color: #6c757d;
    font-family: Arial, sans-serif;
  }
}
* { box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt; color: #212529; line-height: 1.55; }

h1 { font-size: 28pt; color: #0d6efd; margin: 0 0 6pt; }
h2 { font-size: 16pt; color: #0d6efd; border-bottom: 2px solid #0d6efd; padding-bottom: 4pt;
     margin-top: 22pt; margin-bottom: 8pt; page-break-before: always; }
h2.no-break { page-break-before: avoid; }
h3 { font-size: 13pt; color: #198754; margin-top: 14pt; margin-bottom: 5pt; }
h4 { font-size: 11pt; color: #495057; margin-top: 10pt; margin-bottom: 4pt; }

p  { margin: 0 0 7pt; }
ul, ol { margin: 0 0 7pt; padding-left: 20pt; }
li { margin-bottom: 3pt; }

code { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px;
       padding: 1px 5px; font-size: 9.5pt; font-family: "Courier New", monospace; color: #d63384; }

.cover { text-align: center; padding-top: 60pt; }
.cover h1 { font-size: 32pt; }
.cover .sub  { font-size: 14pt; color: #495057; margin-top: 6pt; }
.cover .ver  { font-size: 10pt; color: #adb5bd; margin-top: 40pt; }
.cover .logo { font-size: 52pt; margin-bottom: 10pt; }

.toc-entry { display: flex; justify-content: space-between; padding: 3pt 0;
             border-bottom: 1px dotted #dee2e6; font-size: 10.5pt; }
.toc-entry span { color: #6c757d; }

.req-box { background: #e8f4fd; border-left: 4px solid #0d6efd; border-radius: 0 6px 6px 0;
           padding: 7pt 12pt; margin-bottom: 10pt; }
.req-box b { color: #0d6efd; }

.step { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px;
        padding: 8pt 12pt; margin: 6pt 0; }
.step-num { display: inline-block; background: #0d6efd; color: #fff; border-radius: 50%;
            width: 20pt; height: 20pt; line-height: 20pt; text-align: center;
            font-size: 9pt; font-weight: bold; margin-right: 8pt; }
.step-title { font-weight: bold; color: #212529; }

.screenshot {
  border: 1px solid #ced4da;
  border-radius: 6px;
  overflow: hidden;
  margin: 10pt 0;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,.10);
  page-break-inside: avoid;
}
.screen-title {
  background: #343a40;
  color: #fff;
  font-size: 10.5pt;
  font-weight: bold;
  padding: 6pt 12pt;
  font-family: Arial, sans-serif;
}
.screen-nav {
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  padding: 5pt 12pt;
  font-size: 10.5pt;
}

.tbl { width: 100%; border-collapse: collapse; font-size: 10pt; }
.tbl th { background: #343a40; color: #fff; padding: 5pt 8pt; text-align: left; font-size: 10pt; }
.tbl td { padding: 4pt 8pt; border-bottom: 1px solid #dee2e6; }
.tbl tr:nth-child(even) td { background: #f8f9fa; }

.badge-green  { background:#198754; color:#fff; padding:2px 8px; border-radius:10px; font-size:9pt; }
.badge-blue   { background:#0d6efd; color:#fff; padding:2px 8px; border-radius:10px; font-size:9pt; }
.badge-orange { background:#fd7e14; color:#fff; padding:2px 8px; border-radius:10px; font-size:9pt; }
.badge-red    { background:#dc3545; color:#fff; padding:2px 8px; border-radius:10px; font-size:9pt; }
.badge-gray   { background:#6c757d; color:#fff; padding:2px 8px; border-radius:10px; font-size:9pt; }

.alert-info    { background:#cff4fc; border:1px solid #9eeaf9; border-radius:6px; padding:8pt 12pt; margin:8pt 0; }
.alert-success { background:#d1e7dd; border:1px solid #a3cfbb; border-radius:6px; padding:8pt 12pt; margin:8pt 0; }
.alert-warning { background:#fff3cd; border:1px solid #ffda6a; border-radius:6px; padding:8pt 12pt; margin:8pt 0; }
.alert-danger  { background:#f8d7da; border:1px solid #f1aeb5; border-radius:6px; padding:8pt 12pt; margin:8pt 0; }

.api-endpoint { background:#1e1e2e; color:#cdd6f4; border-radius:6px; padding:8pt 12pt;
                font-family:"Courier New",monospace; font-size:9.5pt; margin:6pt 0; }
.api-method-get    { color:#a6e3a1; font-weight:bold; }
.api-method-post   { color:#89b4fa; font-weight:bold; }
.api-method-put    { color:#f9e2af; font-weight:bold; }
.api-method-delete { color:#f38ba8; font-weight:bold; }

table.params { width:100%; border-collapse:collapse; font-size:10pt; margin:6pt 0; }
table.params th { background:#495057; color:#fff; padding:4pt 8pt; }
table.params td { padding:4pt 8pt; border:1px solid #dee2e6; vertical-align:top; }
table.params td:first-child { font-family:"Courier New",monospace; color:#d63384; white-space:nowrap; }
"""

# ── HTML sections ─────────────────────────────────────────────────────────────

def cover():
    return """
<div class="cover">
  <div class="logo">&#128247;</div>
  <h1>Device Management System</h1>
  <p class="sub">Complete User Manual</p>
  <p style="color:#6c757d;margin-top:12pt;font-size:11pt;">
    WebSocket SDK &mdash; Django Web Application
  </p>
  <br><br>
  <table style="margin:0 auto;border-collapse:collapse;font-size:10.5pt;">
    <tr><td style="padding:4pt 12pt;color:#6c757d;text-align:right;">Version</td>
        <td style="padding:4pt 12pt;font-weight:bold;">2.0</td></tr>
    <tr><td style="padding:4pt 12pt;color:#6c757d;text-align:right;">Platform</td>
        <td style="padding:4pt 12pt;font-weight:bold;">Django 4.2 &bull; Python 3.11+</td></tr>
    <tr><td style="padding:4pt 12pt;color:#6c757d;text-align:right;">Devices</td>
        <td style="padding:4pt 12pt;font-weight:bold;">TC5000 / M50 / M91 &amp; compatible</td></tr>
    <tr><td style="padding:4pt 12pt;color:#6c757d;text-align:right;">Protocol</td>
        <td style="padding:4pt 12pt;font-weight:bold;">WebSocket XML SDK</td></tr>
  </table>
  <p class="ver">Generated automatically &bull; All Rights Reserved</p>
</div>
<div style="page-break-after:always;"></div>
"""

def toc():
    entries = [
        ("1", "System Overview & Architecture", "3"),
        ("2", "Device Management", "4"),
        ("3", "How to Set Up a Device", "5"),
        ("4", "Add a Device to the Registry", "6"),
        ("5", "Assign a Device to a Zone / Area", "7"),
        ("6", "Clear Data from a Device", "8"),
        ("7", "Transfer Data Between Devices (Manual Sync)", "9"),
        ("8", "Face / Fingerprint / Card Data — Automatic Sync", "11"),
        ("9", "Remote Handling of Device Menu", "12"),
        ("10", "Remote Enrollment (Face, Fingerprint, Card)", "13"),
        ("11", "Device Connect / Disconnect Logging", "14"),
        ("12", "Time Zone Access per Employee", "15"),
        ("13", "Add and Delete Employees", "16"),
        ("14", "Delete Logs by Period", "18"),
        ("15", "Download Logs — Automatic and Manual", "19"),
        ("16", "Time Synchronisation", "21"),
        ("17", "Enable and Disable Users", "22"),
        ("18", "Name Upload to Device", "23"),
        ("19", "Auto-Upload New Employee to All Devices", "24"),
        ("20", "Date / Time Employee Block", "25"),
        ("21", "Restart Device from Software", "26"),
        ("22", "Interlock", "27"),
        ("23", "API Integration for External Software", "29"),
    ]
    rows = "".join(
        f"<div class='toc-entry'><span><b>{n}.</b>&nbsp; {t}</span><span>{p}</span></div>"
        for n, t, p in entries
    )
    return f"""
<h2 class="no-break" style="page-break-before:avoid;">Table of Contents</h2>
{rows}
<div style="page-break-after:always;"></div>
"""

def sec1():
    return """
<h2>1. System Overview &amp; Architecture</h2>
<p>The <b>Device Management System</b> is a Django-based web application that communicates with
biometric access-control devices (fingerprint readers, face-recognition terminals, card readers)
over a persistent WebSocket connection managed by the <b>Device Broker</b> service.</p>

<h3>Architecture Diagram</h3>
<div class="screenshot">
  <div class="screen-title">System Architecture</div>
  <div style="padding:14pt 16pt;font-family:'Courier New',monospace;font-size:10pt;line-height:1.9;background:#1e1e2e;color:#cdd6f4;">
    ┌─────────────────────────────────────────────────────────────────┐<br>
    │&nbsp;&nbsp;&nbsp;<span style="color:#89b4fa;">BIOMETRIC DEVICES</span> (TC5000 / M50 / M91)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;[Device A] [Device B] [Device C] ... [Device N]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    └──────────────────────────┬──────────────────────────────────────┘<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│ WebSocket (XML SDK)<br>
    ┌─────────────────────────────────────────────────────────────────┐<br>
    │&nbsp;&nbsp;&nbsp;<span style="color:#a6e3a1;">DEVICE BROKER</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;• Register/Login handshake&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;• Command routing (send &amp; receive XML)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;• Push log events to Django via HTTP&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    └──────────────────────────┬──────────────────────────────────────┘<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│ Unix socket / TCP<br>
    ┌─────────────────────────────────────────────────────────────────┐<br>
    │&nbsp;&nbsp;&nbsp;<span style="color:#f9e2af;">DJANGO WEB APPLICATION</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;• UI: Zones, Devices, Employees, Logs, Sync, API Keys&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;• REST API: /api/v1/ (X-API-Key auth)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    │&nbsp;&nbsp;&nbsp;• Database: SQLite / PostgreSQL&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    └─────────────────────────────────────────────────────────────────┘<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│ HTTP/HTTPS<br>
    ┌─────────────────────────────────────────────────────────────────┐<br>
    │&nbsp;&nbsp;&nbsp;<span style="color:#cba6f7;">EXTERNAL SOFTWARE</span> (HR, Payroll, ERP) via REST API&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
    └─────────────────────────────────────────────────────────────────┘<br>
  </div>
</div>

<h3>Starting the System</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Start the Device Broker:</span>
<code>python -m devicebroker</code></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Start the Django web server:</span>
<code>python manage.py runserver 0.0.0.0:8000</code></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Open the web UI in a browser:</span>
<code>http://&lt;server-ip&gt;:8000/</code></div>

<div class="alert-info">
  <b>&#x2139; Tip:</b> Use <code>start_all.py</code> or <code>start_all.sh</code> in the root of the project to launch both services at once.
</div>
"""

def sec2():
    nav = nav_bar("Home", "&#9654; Online Devices", "Manage &#9660;", "Logs &#9660;", "API Keys")
    scr = table_screen("Online Devices — Live View",
        ["Device ID (Serial)", "Connection ID", "Terminal Type", "Product Name", ""],
        [
            ["TC5000-A1B2C3", "0", "Fingerprint+Face", "TC5000", "&#128279; Open"],
            ["M50-001122", "1", "Face Recognition", "M50-Pro", "&#128279; Open"],
            ["M91-AABBCC", "2", "Card+Fingerprint", "M91 DE", "&#128279; Open"],
        ],
        note="Green row = device is online. Click 'Open' to access all controls for that device."
    )
    return f"""
<h2>2. Device Management</h2>
<div class="req-box"><b>Requirement 1 &amp; 2:</b> Device Management — view all connected devices, their type, serial number, and status in real time.</div>

<p>The <b>Online Devices</b> page shows every biometric terminal currently connected to the system via WebSocket.
Devices appear automatically when they connect and are removed when they disconnect.</p>

<h3>How to Access</h3>
<ol>
  <li>Open the web application in your browser.</li>
  <li>Click <b>Online Devices</b> in the top navigation bar.</li>
  <li>The table shows all currently connected devices with their serial number (Device ID), connection slot, type, and model name.</li>
</ol>

{nav}
{scr}

<h3>Device Control Panel</h3>
<p>Clicking <b>Open</b> for any device navigates to the full <b>Device Control Panel</b> which exposes
all remote operations: user management, biometric data, logs, settings, sync, restart, and more.</p>

{screen("Device Control Panel — TC5000-A1B2C3", [
    ("Device ID", "TC5000-A1B2C3"),
    ("Terminal Type", "Fingerprint+Face"),
    ("Product Name", "TC5000"),
    "---",
    "► Device Status / Info / Misc Controls",
    "► Ethernet Settings | Wi-Fi Settings | NTP Settings",
    "---",
    "► User Management | Face Data | Fingerprints | Card/QR/Password",
    "► Remote Enroll | Enroll Face by Photo",
    "---",
    "► Access Timezone Settings | Lock Control",
    "► Attendance Logs | Clear Data",
    "► Bulk Download Logs | Restart Device",
])}
"""

def sec3():
    return f"""
<h2>3. How to Set Up a Device</h2>
<div class="req-box"><b>Requirement 2:</b> Procedure for connecting a physical device to the software system.</div>

<h3>Prerequisites</h3>
<ul>
  <li>Device must be on the same network (LAN / VPN) as the server, or reachable over the internet.</li>
  <li>The Device Broker and Django web application must be running.</li>
</ul>

<h3>Step-by-Step Setup</h3>

<div class="step"><span class="step-num">1</span><span class="step-title">Configure the Server URL on the Device</span>
<p style="margin:6pt 0 0 28pt;">On the physical device, go to <b>Settings → Network → Server URL</b> (or use the <b>Server URL Settings</b> page in the web UI under Device → Server URL Settings) and enter:</p>
<code>ws://&lt;server-ip&gt;:8765</code>
</div>

<div class="step"><span class="step-num">2</span><span class="step-title">Device Connects and Registers</span>
<p style="margin:6pt 0 0 28pt;">The device initiates a WebSocket connection to the broker. The broker sends a Registration request to Django, which creates a <b>DeviceRegistry</b> record automatically and issues a unique token.</p>
</div>

<div class="step"><span class="step-num">3</span><span class="step-title">Device Logs In</span>
<p style="margin:6pt 0 0 28pt;">The device sends its serial number and token. Django validates the token. On success, the device appears in the <b>Online Devices</b> list.</p>
</div>

<div class="step"><span class="step-num">4</span><span class="step-title">Verify in Device Registry</span>
<p style="margin:6pt 0 0 28pt;">Navigate to <b>Manage → Device Registry</b>. The new device will have <span class="badge-green">Online</span> status and a <code>last_seen</code> timestamp.</p>
</div>

{screen("Device Registration Flow", [
    ("Step 1", "Device sends: Register (SN=TC5000-A1B2C3)"),
    ("Step 2", "Server responds: token=b3de3cba5801…"),
    ("Step 3", "Device sends: Login (SN=TC5000-A1B2C3, token=b3de3cba…)"),
    ("Step 4", "Server responds: OK — device is now online"),
    ("Step 5", "Django creates/updates DeviceRegistry record"),
    ("Step 6", "Connection event logged: Connected at 2026-04-23 10:15:00"),
], note="Tokens are persisted in the DeviceRegistry table. A device that reconnects uses the same token.")}

<div class="alert-success">
  <b>&#10003; Verification:</b> After setup, the device serial number appears in <b>Online Devices</b> and in <b>Device Registry</b> with status Online and a recent Last Seen time.
</div>
"""

def sec4():
    return f"""
<h2>4. Add a Device to the Registry</h2>
<div class="req-box"><b>Requirement 3:</b> Pre-register or manually add a device so it can be given a name, assigned to a zone, and configured before it connects.</div>

<p>Devices auto-register on first connection, but you can also pre-add them manually to assign a friendly name, location, and zone ahead of time.</p>

<h3>How to Add a Device Manually</h3>

<div class="step"><span class="step-num">1</span><span class="step-title">Navigate to Device Registry</span>
<p style="margin:4pt 0 0 28pt;">Click <b>Manage → Device Registry</b> in the top navigation bar.</p>
</div>

<div class="step"><span class="step-num">2</span><span class="step-title">Click "+ Add Device"</span>
<p style="margin:4pt 0 0 28pt;">Click the blue <b>+ Add Device</b> button in the top-right corner.</p>
</div>

<div class="step"><span class="step-num">3</span><span class="step-title">Fill in the Device Details</span>
</div>

{screen("Add Device Form", [
    ("Serial Number *", "TC5000-ENTRANCE-01   ← exact SN printed on device"),
    ("Friendly Name", "Main Entrance Reader"),
    ("Location", "Building A, Ground Floor"),
    ("Zone", "[ Ground Floor Zone  ▼ ]"),
    ("Active", "☑ Yes (device can log in)"),
    ("Interlock Enabled", "☐ (enable for interlock feature)"),
], buttons=[("Save", "#0d6efd"), ("Cancel", "#6c757d")],
note="Serial Number must exactly match the SN printed on the physical device label.")}

<div class="step"><span class="step-num">4</span><span class="step-title">Click Save</span>
<p style="margin:4pt 0 0 28pt;">The device record is created. When the physical device connects, it will use this record for authentication and inherit the zone and name settings.</p>
</div>

{table_screen("Device Registry — After Adding",
    ["Serial Number", "Name", "Zone", "Location", "Status", "Interlock", "Last Seen"],
    [
        ["TC5000-ENTRANCE-01", "Main Entrance Reader", "Ground Floor", "Building A, GF", "&#x1F7E1; Offline", "OFF", "—"],
        ["M50-001122", "Cafeteria Door", "1st Floor", "Building B", "&#x1F7E2; Online", "ON", "2026-04-23 10:15"],
    ]
)}
"""

def sec5():
    return f"""
<h2>5. Assign a Device to a Zone / Area</h2>
<div class="req-box"><b>Requirement 4:</b> Organise devices into physical zones (areas) for zone-wise sync, reporting, and interlock grouping.</div>

<h3>Step 1 — Create a Zone</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Go to Manage → Zones / Areas</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click "+ New Zone"</span></div>

{screen("Create Zone Form", [
    ("Zone Name *", "Ground Floor"),
    ("Description", "All entrance and exit readers on ground floor"),
], buttons=[("Save", "#0d6efd"), ("Cancel", "#6c757d")])}

<div class="step"><span class="step-num">3</span><span class="step-title">Click Save</span>
<p style="margin:4pt 0 0 28pt;">The zone is created and appears in the Zones list.</p>
</div>

<h3>Step 2 — Assign Devices to the Zone</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Go to Manage → Device Registry</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Edit</b> next to the device you want to assign</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Change the <b>Zone</b> dropdown to the desired zone and click Save</span></div>

{table_screen("Zones List", ["Zone Name", "Description", "Device Count", "Actions"],
    [
        ["Ground Floor", "All entrance/exit on ground floor", "3 devices", "Edit | Sync | Delete"],
        ["1st Floor", "Office area readers", "5 devices", "Edit | Sync | Delete"],
        ["Parking", "Parking barrier readers", "2 devices", "Edit | Sync | Delete"],
    ],
    note="The 'Sync' button triggers a bidirectional sync of all online devices in that zone."
)}

<div class="alert-info">
  <b>&#x2139; Tip:</b> You can trigger a zone-wide user sync (face, fingerprint, card data) by clicking the <b>Sync</b> button next to any zone. See Section 8 for details.
</div>
"""

def sec6():
    return f"""
<h2>6. Clear Data from a Device</h2>
<div class="req-box"><b>Requirement 5:</b> Remotely erase user data, attendance logs, management logs, or all data from a selected device.</div>

<h3>How to Clear Device Data</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open the device from Online Devices → Open</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Scroll to Maintenance → click <b>Clear Data</b></span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Choose what to clear and click the corresponding button</span></div>

{screen("Clear Data Page — TC5000-A1B2C3", [
    ("⚠ Warning", "These operations are irreversible on the device."),
    "---",
    ("Clear User Enrollment Data", "Removes all user profiles + biometric templates"),
    ("Take Off Managers", "Demotes all manager/admin privileges"),
    ("Clear Attendance Logs", "Deletes all time-attendance records on device"),
    ("Clear Management Logs", "Deletes all admin action logs on device"),
    ("Clear All Data", "Wipes everything (users + all logs)"),
], buttons=[
    ("Clear User Data", "#fd7e14"),
    ("Take Off Managers", "#6c757d"),
    ("Clear Attendance Logs", "#dc3545"),
    ("Clear Mgmt Logs", "#dc3545"),
    ("Clear ALL", "#dc3545"),
], note="Local database logs are NOT affected — only the data stored on the physical device is cleared.")}

<div class="alert-warning">
  <b>&#9888; Warning:</b> <b>Clear ALL</b> permanently removes all users and biometric data from the device.
  Use <b>Sync Users</b> afterward to restore users from another device or the local employee registry.
</div>
"""

def sec7():
    return f"""
<h2>7. Transfer Data Between Devices</h2>
<div class="req-box"><b>Requirement 6:</b> Manually copy user data (profile, fingerprints, face, photo, card, password) from one device to one or more others — or bidirectionally across all devices. Zone-wise transfer is also supported.</div>

<p>The system supports three sync modes, all accessed from <b>Manage → Sync Users</b>:</p>

<h3>Sync Modes Explained</h3>
<table class="tbl">
  <thead><tr><th>Mode</th><th>Direction</th><th>Effect on Target</th><th>Use Case</th></tr></thead>
  <tbody>
    <tr><td><b>Merge</b></td><td>Host → Targets</td><td>Adds/updates users. Extra users on target are left untouched.</td><td>Add new users from one device to others</td></tr>
    <tr><td><b>Mirror</b></td><td>Host → Targets</td><td>Flushes target first, then copies exactly. Target becomes a copy of host.</td><td>Replace all data on a target with a trusted source</td></tr>
    <tr><td><b>Bidirectional</b></td><td>All ↔ All</td><td>Every selected device gets every user. No deletions.</td><td>Initial setup across multiple new devices</td></tr>
  </tbody>
</table>

<h3>How to Perform a Manual Sync</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click Manage → Sync Users</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Choose a Sync Mode (Merge / Mirror / Bidirectional)</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Select the Host device (source)</span></div>
<div class="step"><span class="step-num">4</span><span class="step-title">Select one or more Target devices (hold Ctrl/Cmd for multiple)</span></div>
<div class="step"><span class="step-num">5</span><span class="step-title">Click "Run Sync" — wait for the log to appear</span></div>

{screen("Sync Users Page", [
    ("Sync Mode", "( ) Merge   ( ) Mirror   (●) Bidirectional"),
    "---",
    ("Host Device", "TC5000-A1B2C3  (conn=0)   [not needed for Bidirectional]"),
    "---",
    ("Target Devices", "☑ TC5000-A1B2C3  (conn=0)"),
    ("", "☑ M50-001122    (conn=1)"),
    ("", "☑ M91-AABBCC    (conn=2)"),
], buttons=[("⟷ Run Bidirectional Merge", "#198754")],
note="Hold Ctrl/Cmd to select multiple targets. Mirror mode will warn before deleting extra users.")}

{screen("Sync Log Output", [
    ("", "=============================================="),
    ("", "BIDIRECTIONAL SYNC: ['TC5000-A1B2C3', 'M50-001122', 'M91-AABBCC']"),
    ("", "=============================================="),
    ("", "Pulling from TC5000-A1B2C3..."),
    ("", "  Found 12 user profiles"),
    ("", "  UID=1001  Name=set  Fingers=2  Face=Yes"),
    ("", "  UID=1002  Name=set  Fingers=3  Face=Yes"),
    ("", "Pulling from M50-001122...  Found 8 users"),
    ("", "Merged master: 15 unique users"),
    ("", "M91-AABBCC: Pushing 5 missing users..."),
    ("", "  Push UID=1010: Profile + name + credentials: OK"),
    ("", "  Push UID=1010: Face: OK"),
    ("", "BIDIRECTIONAL SYNC COMPLETE"),
])}

<h3>Zone-Wise Sync</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Go to Manage → Zones / Areas</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Sync</b> next to the target zone</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Start Zone Sync</b> — all online devices in the zone are synced bidirectionally</span></div>

{screen("Zone Sync — Ground Floor", [
    ("Zone", "Ground Floor"),
    ("Devices in Zone", "TC5000-ENTRANCE-01, TC5000-EXIT-01, M50-LOBBY"),
    ("Online Devices Found", "3 of 3"),
    ("Action", "Bidirectional merge across all 3 devices"),
], buttons=[("Start Zone Sync", "#0d6efd")])}

<div class="alert-info"><b>&#x2139; Data transferred includes:</b> User profile, name, department, access timesets, card number, password, QR code, all 10 fingerprint slots, face template, and user photo.</div>
"""

def sec8():
    return f"""
<h2>8. Face / Fingerprint / Card Data — Automatic Sync</h2>
<div class="req-box"><b>Requirement 7:</b> Face, fingerprint, and card data are automatically synchronised across all devices when using the Employee registry or the Sync engine.</div>

<h3>Automatic Sync Mechanisms</h3>
<table class="tbl">
  <thead><tr><th>Trigger</th><th>What Happens</th><th>Data Included</th></tr></thead>
  <tbody>
    <tr><td>New employee saved (Manage → Employees)</td><td>Profile pushed to ALL currently online devices immediately</td><td>Name, card, timesets, period, privilege</td></tr>
    <tr><td>Employee edited</td><td>Updated profile pushed to ALL online devices</td><td>All changed fields</td></tr>
    <tr><td>Manual Sync (Manage → Sync Users)</td><td>Full biometric sync between selected devices</td><td>Profile + fingerprints + face + photo + card</td></tr>
    <tr><td>Zone Sync</td><td>Bidirectional sync across all devices in a zone</td><td>Profile + fingerprints + face + photo + card</td></tr>
  </tbody>
</table>

<h3>How to Verify Automatic Sync</h3>
<ol>
  <li>Add or edit an employee in <b>Manage → Employees</b> and click <b>Save &amp; Push to Devices</b>.</li>
  <li>Open any online device → <b>User Management</b>.</li>
  <li>Enter the same Employee ID and click <b>Read User</b> — the data should appear on the device.</li>
</ol>

{screen("Employee Push Result", [
    ("Action", "Save employee EMP-1005 'John Smith'"),
    ("Devices Online", "TC5000-A1B2C3, M50-001122"),
    ("Push to TC5000-A1B2C3", "✔ OK — SetUserData accepted"),
    ("Push to M50-001122", "✔ OK — SetUserData accepted"),
    ("Biometric sync status", "Use Sync Users to push face/fingerprint data"),
], note="Profile data (name, card, department, timesets) is pushed immediately. Biometric templates (face/fingerprint) require manual sync or enrollment on the device.")}

<h3>Enrolling Biometrics After Auto-Push</h3>
<p>After the employee profile is pushed, enroll biometrics remotely (see Section 10) or let the employee enroll directly on the device.</p>
"""

def sec9():
    return f"""
<h2>9. Remote Handling of Device Menu</h2>
<div class="req-box"><b>Requirement 8:</b> Enable or disable the device from the software, effectively locking or unlocking the device interface and preventing local operation.</div>

<p>The software allows you to remotely <b>enable</b> or <b>disable</b> a device's verification interface. When disabled, the device will not process punches or allow enrolment.</p>

<h3>How to Enable / Disable a Device</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open the device (Online Devices → Open)</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Status / Info / Misc Controls</b></span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Use the <b>Disable Device</b> or <b>Enable Device</b> button</span></div>

{screen("Status / Info / Misc Controls", [
    ("Current Time on Device", "2026-04-23 10:15:30"),
    ("Device Status", "Door: Closed  |  Alarm: None"),
    "---",
    ("Actions", ""),
], buttons=[
    ("Disable Device", "#dc3545"),
    ("Enable Device", "#198754"),
    ("Get Time", "#6c757d"),
    ("Set Time (sync)", "#0d6efd"),
    ("Get Status", "#6c757d"),
    ("Get Info", "#6c757d"),
])}

<h3>Lock Control (Advanced)</h3>
<p>For lock/door control, navigate to <b>Access Control → Lock Control</b> on the device control panel.</p>

{screen("Lock Control", [
    ("Lock Control Mode", "[ Auto Recover    ▼ ]"),
    ("Available Modes", "Force Open | Force Close | Normal Open | Auto Recover | Restart | Cancel Warning | Illegal Open"),
], buttons=[("Read Mode", "#6c757d"), ("Apply Mode", "#fd7e14")])}

<div class="alert-info"><b>&#x2139; Note:</b> <b>Restart</b> is available as a dedicated one-click button on the main device control page (see Section 21). All other lock modes are in the Lock Control page.</div>
"""

def sec10():
    return f"""
<h2>10. Remote Enrollment — Face, Fingerprint, Card</h2>
<div class="req-box"><b>Requirement 9:</b> Remotely trigger enrollment of face, fingerprint, or card for a specific user ID without physically touching the device.</div>

<h3>Method 1 — Remote Enroll (on-device screen)</h3>
<p>This method instructs the device to display an enrolment prompt on its own screen so the employee can enrol there.</p>

<div class="step"><span class="step-num">1</span><span class="step-title">Device Control Panel → User Data → <b>Remote Enroll</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Enter the User ID and select the enrolment type</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Start Enroll</b> — device screen prompts the employee</span></div>
<div class="step"><span class="step-num">4</span><span class="step-title">Click <b>Query Status</b> to check completion, then <b>Stop Enroll</b></span></div>

{screen("Remote Enroll Page", [
    ("User ID", "1005"),
    ("Enrolment Type", "(●) Face   ( ) Fingerprint   ( ) Card   ( ) QR"),
    ("Finger Slot (if FP)", "[ Slot 0 ▼ ]  (0–9, left/right hand fingers)"),
    ("Duplication Check", "☑ Yes"),
    "---",
    ("Status", "Awaiting employee on device screen..."),
], buttons=[("Start Enroll", "#198754"), ("Query Status", "#0d6efd"), ("Stop Enroll", "#dc3545")])}

<h3>Method 2 — Enroll Face by Photo Upload</h3>
<p>Upload a JPEG/PNG photo of the employee to enrol their face template remotely.</p>

<div class="step"><span class="step-num">1</span><span class="step-title">Device Control Panel → User Data → <b>Enroll Face by Photo</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Enter the User ID and paste the Base64-encoded photo data</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Enroll</b></span></div>

{screen("Enroll Face by Photo", [
    ("User ID", "1005"),
    ("Photo Data (Base64)", "/9j/4AAQSkZJRgABAQAAAQABAAD/...  [truncated]"),
], buttons=[("Enroll Face", "#198754")],
note="The device extracts the face feature vector from the photo and stores the template. Best results with a clear front-facing photo.")}

<h3>Managing Biometric Data Directly</h3>
<p>Use the dedicated pages under <b>User Data</b> on the device control panel:</p>
<ul>
  <li><b>Manage Face Data</b> — Read / Write / Delete face templates</li>
  <li><b>Manage Fingerprints</b> — Read / Write / Delete any of the 10 fingerprint slots</li>
  <li><b>View Password / Card / QR</b> — Read card number, QR code, password from a user</li>
</ul>
"""

def sec11():
    return f"""
<h2>11. Device Connect / Disconnect Logging</h2>
<div class="req-box"><b>Requirement 10:</b> Every time a device connects to or disconnects from the system, the event is logged with a timestamp and stored in the database.</div>

<h3>How Connection Events are Logged</h3>
<p>When a device logs in successfully, the Device Broker posts a <code>connect</code> event to Django.
When the WebSocket connection closes, a <code>disconnect</code> event is posted. Both are stored in the <b>DeviceConnectionLog</b> table.</p>

<h3>How to View Connection Logs</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Manage → Connection Logs</b> in the top navigation bar</span></div>

{table_screen("Device Connection Logs", ["Timestamp", "Device ID", "Event"],
    [
        ["2026-04-23 10:15:02", "TC5000-A1B2C3", "&#x1F7E2; Connected"],
        ["2026-04-23 09:58:11", "M50-001122", "&#x1F534; Disconnected"],
        ["2026-04-23 09:58:00", "M50-001122", "&#x1F7E2; Connected"],
        ["2026-04-23 08:30:45", "M91-AABBCC", "&#x1F7E2; Connected"],
        ["2026-04-22 23:01:10", "TC5000-A1B2C3", "&#x1F534; Disconnected"],
    ],
    note="The 200 most recent events are shown. Green = Connected, Grey = Disconnected."
)}

<div class="alert-info">
<b>&#x2139; Where stored:</b> The <code>DeviceConnectionLog</code> table in the database. The <code>DeviceRegistry</code> record for each device is also updated with the <code>last_seen</code> timestamp on each connect.
</div>
"""

def sec12():
    return f"""
<h2>12. Time Zone Access per Employee</h2>
<div class="req-box"><b>Requirement 11:</b> Each employee can be assigned up to 5 access time zones that define which hours of each day of the week they are allowed to access a device.</div>

<h3>Step 1 — Define an Access Timezone Schedule</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open a device → Access Control → <b>Access Timezone Settings</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Enter a Timezone Number (1–50) and define the time sections for each day</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Write Settings</b></span></div>

{screen("Access Timezone Settings", [
    ("Timezone Number", "1"),
    "---",
    ("Sunday (Section 0)",    "Start: 0   End: 0   (= no access)"),
    ("Monday (Section 1)",    "Start: 480  End: 1080  (08:00 – 18:00)"),
    ("Tuesday (Section 2)",   "Start: 480  End: 1080"),
    ("Wednesday (Section 3)", "Start: 480  End: 1080"),
    ("Thursday (Section 4)",  "Start: 480  End: 1080"),
    ("Friday (Section 5)",    "Start: 480  End: 1080"),
    ("Saturday (Section 6)",  "Start: 0   End: 0   (= no access)"),
], buttons=[("Read Settings", "#6c757d"), ("Write Settings", "#0d6efd")],
note="Times are in minutes since midnight. 480 = 08:00, 1080 = 18:00. 0,0 means no access that day.")}

<h3>Step 2 — Assign Timezone to an Employee</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open a device → User Management → enter User ID → Read User</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Set <b>Timeset 1</b> to the timezone number (e.g. 1) and leave others at -1</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Write User</b></span></div>

{screen("User Management — Timeset Assignment", [
    ("User ID", "1005"),
    ("Name", "John Smith"),
    ("Timeset 1", "1   ← timezone #1 (Mon-Fri 08:00-18:00)"),
    ("Timeset 2", "-1  (not set)"),
    ("Timeset 3", "-1"),
    ("Timeset 4", "-1"),
    ("Timeset 5", "-1"),
], buttons=[("Read User", "#6c757d"), ("Write User", "#0d6efd")])}

<p>Or assign via <b>Manage → Employees → Edit Employee → Timeset 1–5</b> fields — this pushes to all devices automatically.</p>
"""

def sec13():
    return f"""
<h2>13. Add and Delete Employees</h2>
<div class="req-box"><b>Requirement 12:</b> Add new employees or delete existing ones from the software. Changes are automatically pushed to all connected devices.</div>

<h3>Adding an Employee</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Manage → Employees</b> in the top navigation bar</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>+ Add Employee</b></span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Fill in the employee details</span></div>

{screen("Add Employee Form", [
    ("Employee ID *", "1006"),
    ("Name *", "Priya Sharma"),
    ("Department", "3"),
    ("Privilege", "[ User ▼ ]   (User / Manager / Administrator)"),
    ("Enabled", "☑ Yes"),
    ("Card Number", "A2B3C4D5"),
    ("Password", "1234"),
    ("Period Start (block start)", "2026-01-01"),
    ("Period End (block end)",     "2026-12-31"),
    ("Timeset 1", "1"),
    ("Timeset 2–5", "-1"),
], buttons=[("Save & Push to Devices", "#0d6efd"), ("Cancel", "#6c757d")],
note="Clicking 'Save & Push to Devices' immediately sends this employee's profile to ALL currently online devices.")}

<div class="step"><span class="step-num">4</span><span class="step-title">Click <b>Save &amp; Push to Devices</b></span></div>

{table_screen("Employees List", ["ID", "Name", "Dept", "Privilege", "Enabled", "Card", "Period", "Actions"],
    [
        ["1001", "Ahmed Ali", "1", "User", "&#x1F7E2; Yes", "A1B2C3D4", "—", "Edit | Disable | Delete"],
        ["1005", "John Smith", "2", "Manager", "&#x1F7E2; Yes", "—", "2026-01-01→2026-12-31", "Edit | Disable | Delete"],
        ["1006", "Priya Sharma", "3", "User", "&#x1F7E2; Yes", "A2B3C4D5", "2026-01-01→2026-12-31", "Edit | Disable | Delete"],
    ]
)}

<h3>Deleting an Employee</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Delete</b> next to the employee in the list</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Confirm the deletion on the confirmation page</span></div>

{screen("Delete Employee Confirmation", [
    ("Employee", "1006 — Priya Sharma"),
    ("Warning", "This will delete the employee from the software AND from ALL connected devices."),
], buttons=[("Delete from Software & All Devices", "#dc3545"), ("Cancel", "#6c757d")],
note="The delete command (SetUserData Type=Delete) is sent to every online device before removing the database record.")}

<h3>Deleting from a Single Device (Device-Level)</h3>
<p>To delete a user from only one specific device (not from the employee registry), use the per-device <b>User Management</b> page:</p>
<ol>
  <li>Open the device → User Management</li>
  <li>Enter the User ID and click <b>Read User</b></li>
  <li>Click <b>Delete User</b></li>
</ol>
"""

def sec14():
    return f"""
<h2>14. Delete Logs by Period</h2>
<div class="req-box"><b>Requirement 13:</b> Delete attendance or management logs for a specific date/time range from the local database.</div>

<h3>Method 1 — Delete DB Logs by Date Range</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Logs → Attendance Logs</b> in the top navigation bar</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Fill in the filter fields: Device ID, User ID, Start Time, End Time</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Clear Filtered Logs</b> to delete only the matching records</span></div>

{screen("Attendance Logs — Delete by Period", [
    ("Device ID (optional)", "TC5000-A1B2C3"),
    ("User ID (optional)", "1005"),
    ("Start Time", "2026-01-01 00:00"),
    ("End Time",   "2026-03-31 23:59"),
    "---",
    ("Matched Records", "243 logs found"),
], buttons=[("Search", "#6c757d"), ("Clear Filtered Logs", "#dc3545")],
note="Only logs in the local database are affected. Logs on the device itself are not deleted by this action.")}

<h3>Method 2 — Delete Logs from the Physical Device</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → View Logs (On-Demand Log Fetching) → Attendance Logs</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Get Log Pos Info</b> to see the log position range</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Enter the log position ID up to which you want to delete and click <b>Delete Logs</b></span></div>

{screen("View Device Attendance Logs", [
    ("Log Count on Device", "1842"),
    ("Start Position", "0"),
    ("Max Count", "100000"),
    "---",
    ("Next Log ID (delete up to)", "500"),
], buttons=[
    ("Get First Log", "#6c757d"),
    ("Get Next Log", "#6c757d"),
    ("Get Log Pos Info", "#6c757d"),
    ("Delete Logs", "#dc3545"),
])}

<div class="alert-warning">
  <b>&#9888;</b> On-device deletion removes logs up to a position index, not by date. To delete by date, first fetch logs with a date filter to find the position, then delete up to that position.
</div>

<h3>Delete Management Logs by Period</h3>
<p>Follow the same steps using <b>Logs → Management Logs</b> → filter by date range → <b>Clear Filtered Logs</b>.</p>
"""

def sec15():
    return f"""
<h2>15. Download Logs — Automatic and Manual</h2>
<div class="req-box"><b>Requirement 14 &amp; 15:</b> Attendance logs are downloaded automatically when the device pushes them, and can also be fetched manually with a from/to date range. Both new (real-time) and old (historical) logs are supported.</div>

<h3>Automatic Log Download</h3>
<p>Every time an employee punches in/out on a device, the device immediately pushes the log to the server over the existing WebSocket connection. No manual action is required.</p>

{screen("Automatic Log Flow", [
    ("Step 1", "Employee punches on device"),
    ("Step 2", "Device sends TimeLog XML event to broker"),
    ("Step 3", "Broker posts to Django /device/upload_log"),
    ("Step 4", "Django saves to AttendanceLog table"),
    ("Step 5", "Log visible in Logs → Attendance Logs within seconds"),
])}

<h3>Manual Log Download — Bulk (with Date Range)</h3>
<p>To fetch historical logs stored on a device for a specific date range:</p>

<div class="step"><span class="step-num">1</span><span class="step-title">Open the device control panel → Maintenance → <b>Bulk Download Logs</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Set the Start and End date/time</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Download</b></span></div>

{screen("Bulk Download Logs from Device", [
    ("Start Date/Time", "[ 2026-01-01T00:00  ]"),
    ("End Date/Time",   "[ 2026-03-31T23:59  ]"),
    "---",
    ("Result", "✔ Saved 1,842 log(s) to the database."),
], buttons=[("Download", "#0d6efd")],
note="Leave both fields blank to download ALL logs from the device. Duplicate logs (same device_id + log_id) are skipped automatically.")}

<h3>Manual Log Download — Record by Record (On-Device Fetch)</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → View Logs (On-Demand) → Attendance Logs</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Optionally set User ID, Start Time, End Time filter</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Get First Log</b>, then <b>Get Next Log</b> repeatedly</span></div>

<h3>Export Logs to CSV</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Logs → Export CSV</b> in the top navigation bar</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Optionally add URL filters: <code>?device_id=TC5000-A1B2C3&start=2026-01-01&end=2026-03-31</code></span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">The browser downloads a CSV file</span></div>

{screen("CSV Export URL Examples", [
    ("All logs",       "/logs/download_csv/"),
    ("By device",      "/logs/download_csv/?device_id=TC5000-A1B2C3"),
    ("By date range",  "/logs/download_csv/?start=2026-01-01&end=2026-03-31"),
    ("Combined",       "/logs/download_csv/?device_id=TC5000-A1B2C3&start=2026-01-01&end=2026-03-31"),
], note="CSV columns: ID, Device, LogID, Time, UserID, AttendStatus, Action, AttendOnly, Expired")}
"""

def sec16():
    return f"""
<h2>16. Time Synchronisation</h2>
<div class="req-box"><b>Requirement 16:</b> Synchronise the device clock with the server's current date and time, or configure an NTP server for automatic time sync.</div>

<h3>Method 1 — One-Click Time Sync (Set to Server Time)</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → <b>Status / Info / Misc Controls</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Set Time (Sync)</b> — the device clock is immediately set to the server's current time</span></div>

{screen("Time Sync", [
    ("Current Time on Device", "2026-04-23 09:45:10"),
    ("Server Time", "2026-04-23 10:15:30"),
    ("Time Difference", "30 minutes 20 seconds behind"),
], buttons=[("Get Device Time", "#6c757d"), ("Set Time (Sync to Server)", "#0d6efd")],
note="After clicking 'Set Time', the device clock is updated to match the server's UTC clock instantly.")}

<h3>Method 2 — NTP Server Configuration</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → <b>NTP Server Settings</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Enter the NTP server address, UTC offset, and sync interval</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Write Settings</b></span></div>

{screen("NTP Server Settings", [
    ("NTP Server Address", "pool.ntp.org"),
    ("UTC Timezone Offset", "+330  (= UTC+5:30 for IST)"),
    ("Sync Interval (min)", "60"),
], buttons=[("Read Settings", "#6c757d"), ("Write Settings", "#0d6efd")],
note="UTC offset is in minutes. Examples: +330 = IST (India), +480 = CST (China), 0 = UTC, -300 = EST.")}
"""

def sec17():
    return f"""
<h2>17. Enable and Disable Users</h2>
<div class="req-box"><b>Requirement 17:</b> Enable or disable a specific user across all devices or on a single device. A disabled user cannot punch in.</div>

<h3>Method 1 — Toggle from Employee List (All Devices)</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Manage → Employees</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click the <b>Disable</b> or <b>Enable</b> button next to the employee</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">The system immediately pushes the updated status to <b>all connected devices</b></span></div>

{table_screen("Employees List — Enable/Disable", ["ID", "Name", "Enabled", "Actions"],
    [
        ["1001", "Ahmed Ali", "&#x1F7E2; Yes", "Edit | <b>Disable</b> | Delete"],
        ["1005", "John Smith", "&#x1F534; No", "Edit | <b>Enable</b> | Delete"],
        ["1006", "Priya Sharma", "&#x1F7E2; Yes", "Edit | <b>Disable</b> | Delete"],
    ],
    note="Disabled users appear greyed out. Clicking Disable/Enable immediately updates all connected devices."
)}

<h3>Method 2 — Enable/Disable on a Single Device</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → User Management → enter User ID → Read User</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Change the <b>Enabled</b> field to Yes or No</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Write User</b></span></div>

{screen("User Management — Enable/Disable", [
    ("User ID", "1005"),
    ("Name", "John Smith"),
    ("Enabled", "( ) Yes   (●) No   ← disabled on THIS device only"),
], buttons=[("Write User", "#0d6efd")],
note="This only affects the selected device. Use the Employee list method to push to all devices simultaneously.")}
"""

def sec18():
    return f"""
<h2>18. Name Upload to Device</h2>
<div class="req-box"><b>Requirement 18:</b> Upload an employee's name (and other profile data) to one or more devices.</div>

<p>Employee names are always included when writing user data. The name is encoded in UTF-16LE Base64 format as required by the device firmware.</p>

<h3>How Names are Uploaded</h3>
<table class="tbl">
  <thead><tr><th>Action</th><th>How Name is Sent</th></tr></thead>
  <tbody>
    <tr><td>Add Employee (Manage → Employees)</td><td>Name pushed to all online devices automatically</td></tr>
    <tr><td>Edit Employee</td><td>Name (re-)pushed to all online devices</td></tr>
    <tr><td>User Management → Write User (per device)</td><td>Name sent to that specific device</td></tr>
    <tr><td>Sync Users</td><td>Name transferred to all target devices</td></tr>
  </tbody>
</table>

<h3>Upload Name via User Management (Single Device)</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → User Management</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Enter the User ID and Name</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Write User</b></span></div>

{screen("User Management — Name Upload", [
    ("User ID", "1006"),
    ("Name", "Priya Sharma"),
    ("Privilege", "User"),
    ("Enabled", "Yes"),
    ("Department", "3"),
], buttons=[("Write User", "#0d6efd")],
note="The name is transmitted in UTF-16LE encoding to support all languages including Arabic, Chinese, Hindi, etc.")}
"""

def sec19():
    return f"""
<h2>19. Auto-Upload New Employee to All Devices</h2>
<div class="req-box"><b>Requirement 19:</b> When a new employee is registered in the software, their profile is automatically pushed to all currently connected devices without any manual action.</div>

<h3>How It Works</h3>
<p>When you save a new employee using <b>Manage → Employees → Add Employee</b>, the system:</p>
<ol>
  <li>Saves the employee record to the local database.</li>
  <li>Immediately opens a connection to the Device Broker.</li>
  <li>Calls <code>SetUserData</code> on every currently online device.</li>
  <li>The employee is available on all devices within seconds.</li>
</ol>

{screen("Auto-Upload Flow", [
    ("1. User clicks", "Save & Push to Devices"),
    ("2. DB record created", "Employee ID=1007 'Sara Khan' saved"),
    ("3. Devices online", "TC5000-A1B2C3 (conn=0), M50-001122 (conn=1), M91-AABBCC (conn=2)"),
    ("4. Push TC5000",  "✔ SetUserData → OK"),
    ("4. Push M50",     "✔ SetUserData → OK"),
    ("4. Push M91",     "✔ SetUserData → OK"),
    ("5. Result", "Employee available on 3 devices"),
], note="If a device is offline when the employee is added, use Sync Users later to push to that device.")}

<div class="alert-info">
  <b>&#x2139; What is pushed automatically:</b> Name, privilege, enabled status, department, card number, password, 5 timeset slots, and validity period.<br>
  <b>What requires manual sync:</b> Fingerprint templates and face templates (must be enrolled via Remote Enroll or Sync Users).
</div>
"""

def sec20():
    return f"""
<h2>20. Date / Time Employee Block</h2>
<div class="req-box"><b>Requirement 20:</b> Set a validity period for an employee so that the device automatically denies access before the start date or after the end date.</div>

<p>Every employee record has a <b>Period Start</b> and <b>Period End</b> date. When these are set, the device only allows the employee to punch in during that date window.</p>

<h3>Set a Validity Period for an Employee</h3>

<div class="step"><span class="step-num">1</span><span class="step-title">Go to <b>Manage → Employees</b> and click <b>Edit</b> for the employee</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Set <b>Period Start</b> and <b>Period End</b> dates</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Save &amp; Push to Devices</b></span></div>

{screen("Employee Form — Period Block", [
    ("Employee ID", "1008"),
    ("Name", "Contract Worker A"),
    ("Period Start", "2026-05-01   ← access allowed from this date"),
    ("Period End",   "2026-07-31   ← access blocked after this date"),
    "---",
    ("Result on Device", "Device rejects punch attempts outside 1 May – 31 July 2026"),
], buttons=[("Save & Push to Devices", "#0d6efd")],
note="To block immediately: set Period End to today's date. To unblock: clear both fields.")}

<h3>Set Period via Single-Device User Management</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → User Management → Read User</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Fill in <b>Period Start</b> and <b>Period End</b> fields</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Write User</b></span></div>

<div class="alert-info">
  <b>&#x2139; Combined with Access Timezones (Section 12):</b> Use the Period to control <i>which dates</i> an employee has access, and Access Timezones to control <i>which hours</i> of each day.
</div>
"""

def sec21():
    return f"""
<h2>21. Restart Device from Software</h2>
<div class="req-box"><b>Requirement 21:</b> Remotely restart a biometric device without physical access.</div>

<h3>Method 1 — Dedicated Restart Button (One Click)</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open the device control panel (Online Devices → Open)</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Scroll to <b>Maintenance</b> section at the bottom of the page</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click the <b>Restart Device</b> button</span></div>
<div class="step"><span class="step-num">4</span><span class="step-title">Confirm the restart dialog</span></div>

{screen("Device Control Panel — Maintenance Section", [
    ("Clear Data", "→ Open Clear Data page"),
    ("Firmware Version", "→ Check current firmware"),
    ("Write Firmware", "→ OTA firmware update"),
    ("Bulk Download Logs", "→ Download logs with date range"),
], buttons=[
    ("Clear Data", "#6c757d"),
    ("Firmware Version", "#6c757d"),
    ("Write Firmware", "#6c757d"),
    ("Bulk Download Logs", "#6c757d"),
    ("Restart Device", "#fd7e14"),
],
note="Clicking 'Restart Device' shows a browser confirmation dialog. On confirm, the device reboots within 3-5 seconds.")}

{screen("Restart Confirmation Response", [
    ("Result", '{ "ok": true }'),
    ("Device Status", "Offline (rebooting) → Online (connected) within ~30 seconds"),
])}

<h3>Method 2 — Via Lock Control (Manual Mode)</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Open device → Access Control → Lock Control</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Select <b>Restart</b> from the Mode dropdown</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Click <b>Apply Mode</b></span></div>

<div class="alert-success">
  <b>&#10003; After restart:</b> The device reconnects automatically within 30–60 seconds. A new <span class="badge-green">Connected</span> entry appears in the Device Connection Logs.
</div>
"""

def sec22():
    return f"""
<h2>22. Interlock</h2>
<div class="req-box"><b>Requirement 22:</b> When an employee punches on one interlock-enabled device, access is automatically denied (user disabled) on all other interlock-enabled devices until the next valid punch.</div>

<h3>How Interlock Works</h3>
<p>The Interlock feature prevents "tailgating" — an employee cannot badge into two different doors simultaneously. The logic is:</p>
<ol>
  <li>Employee punches on Device A (interlock enabled).</li>
  <li>The punch event reaches Django via the log upload endpoint.</li>
  <li>Django finds all other online interlock-enabled devices.</li>
  <li>Django returns their connection IDs to the broker.</li>
  <li>The broker sends <code>SetUserData Enabled=No</code> to those devices for that employee.</li>
  <li>The employee cannot punch on any other interlock device until they punch again on a valid device.</li>
</ol>

{screen("Interlock Flow Diagram", [
    ("1. Punch", "EMP-1005 punches on TC5000-ENTRANCE (interlock=ON)"),
    ("2. Log uploaded", "Django receives TimeLog for EMP-1005"),
    ("3. Interlock check", "TC5000-ENTRANCE has interlock=ON → trigger"),
    ("4. Find others", "M50-EXIT (conn=1), M91-CAFETERIA (conn=2) — also interlock=ON"),
    ("5. Deny on M50", "Broker sends SetUserData UserID=1005 Enabled=No → M50"),
    ("6. Deny on M91", "Broker sends SetUserData UserID=1005 Enabled=No → M91"),
    ("7. Result", "EMP-1005 can only exit through the punch sequence"),
])}

<h3>Step 1 — Enable Interlock on Devices</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Go to <b>Manage → Device Registry</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Edit</b> for each device that should participate in interlock</span></div>
<div class="step"><span class="step-num">3</span><span class="step-title">Check <b>Enable Interlock</b> and click Save</span></div>

{screen("Device Registry Edit — Enable Interlock", [
    ("Serial Number", "TC5000-ENTRANCE-01"),
    ("Friendly Name", "Main Entrance Reader"),
    ("Interlock Enabled", "☑ Enable Interlock (deny access on other interlock devices after punch)"),
], buttons=[("Save", "#0d6efd")])}

<h3>Step 2 — Alternatively, Use the Interlock Status Page</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>Manage → Interlock Status</b></span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Click <b>Enable</b> or <b>Disable</b> next to each device</span></div>

{table_screen("Interlock Status Page", ["Device", "Zone", "Interlock", "Action"],
    [
        ["TC5000-ENTRANCE-01 (Main Entrance)", "Ground Floor", "&#x1F7E1; ON", "Disable"],
        ["M50-EXIT-01 (Exit Door)", "Ground Floor", "&#x1F7E1; ON", "Disable"],
        ["M91-CAFETERIA (Cafeteria)", "1st Floor", "&#x26AA; OFF", "Enable"],
    ]
)}

<h3>Step 3 — View Recent Interlock Events</h3>

{table_screen("Interlock Events Log", ["Employee ID", "Punched Device", "Punch Time", "Status"],
    [
        ["1005", "TC5000-ENTRANCE-01", "2026-04-23 09:02:15", "&#x1F7E1; Active"],
        ["1001", "M50-EXIT-01", "2026-04-23 08:58:44", "&#x26AA; Cleared"],
        ["1006", "TC5000-ENTRANCE-01", "2026-04-23 08:45:10", "&#x26AA; Cleared"],
    ]
)}

<div class="alert-warning">
  <b>&#9888; Important:</b> Interlock works in real time as punches occur. For it to function, the Device Broker and Django must be running and the devices must be online.
</div>
"""

def sec23():
    return f"""
<h2>23. API Integration for External Software</h2>
<div class="req-box"><b>Requirement 23:</b> A secure REST API allows HR systems, payroll software, ERP platforms, and other external applications to query and manage the device management system programmatically.</div>

<h3>Authentication</h3>
<p>All API endpoints require an API key passed in the <code>X-API-Key</code> HTTP header (or as a <code>?api_key=</code> URL parameter).</p>

<h3>Step 1 — Generate an API Key</h3>
<div class="step"><span class="step-num">1</span><span class="step-title">Click <b>API Keys</b> in the top navigation bar</span></div>
<div class="step"><span class="step-num">2</span><span class="step-title">Enter a name for the key (e.g., "HR Software") and click <b>Generate New Key</b></span></div>

{table_screen("API Key Management", ["Name", "Key", "Status", "Last Used", "Actions"],
    [
        ["HR Software", "a1b2c3d4e5f6...32chars", "&#x1F7E2; Active", "2026-04-23 10:05", "Disable | Delete"],
        ["Payroll System", "9f8e7d6c5b4a...32chars", "&#x1F7E2; Active", "Never", "Disable | Delete"],
    ]
)}

<h3>REST API Endpoints</h3>

<div class="api-endpoint">
<span class="api-method-get">GET</span>  /api/v1/devices/<br>
<span style="color:#6c7086;">→ List all currently online devices</span><br><br>
<span class="api-method-get">GET</span>  /api/v1/employees/<br>
<span style="color:#6c7086;">→ List all employees in the database</span><br><br>
<span class="api-method-post">POST</span> /api/v1/employees/<br>
<span style="color:#6c7086;">→ Create a new employee and push to all online devices</span><br><br>
<span class="api-method-get">GET</span>  /api/v1/employees/&lt;employee_id&gt;/<br>
<span style="color:#6c7086;">→ Get details for one employee</span><br><br>
<span class="api-method-put">PUT</span>  /api/v1/employees/&lt;employee_id&gt;/<br>
<span style="color:#6c7086;">→ Update an employee and push changes to all devices</span><br><br>
<span class="api-method-delete">DELETE</span> /api/v1/employees/&lt;employee_id&gt;/<br>
<span style="color:#6c7086;">→ Delete employee from DB and all connected devices</span><br><br>
<span class="api-method-get">GET</span>  /api/v1/logs/?device_id=&amp;user_id=&amp;start=&amp;end=<br>
<span style="color:#6c7086;">→ Query attendance logs (up to 500 records)</span><br><br>
<span class="api-method-post">POST</span> /api/v1/sync/<br>
<span style="color:#6c7086;">→ Trigger a device sync (merge / mirror / bidirectional)</span>
</div>

<h3>Example: Create an Employee via API</h3>
<div class="api-endpoint">
<span style="color:#fab387;">curl</span> -X POST https://your-server/api/v1/employees/ \<br>
&nbsp;&nbsp;-H <span style="color:#a6e3a1;">"X-API-Key: a1b2c3d4e5f6..."</span> \<br>
&nbsp;&nbsp;-H <span style="color:#a6e3a1;">"Content-Type: application/json"</span> \<br>
&nbsp;&nbsp;-d <span style="color:#a6e3a1;">'{{"employee_id": 2001, "name": "Ali Hassan", "department": 5, "card": "FFAA1122", "enabled": true}}'</span><br><br>
<span style="color:#6c7086;">Response: 201 Created</span><br>
<span style="color:#a6e3a1;">{{"id": 42, "employee_id": 2001}}</span>
</div>

<h3>Example: Query Logs</h3>
<div class="api-endpoint">
<span style="color:#fab387;">curl</span> "https://your-server/api/v1/logs/?device_id=TC5000-A1B2C3&amp;start=2026-04-01&amp;end=2026-04-23" \<br>
&nbsp;&nbsp;-H <span style="color:#a6e3a1;">"X-API-Key: a1b2c3d4e5f6..."</span><br><br>
<span style="color:#6c7086;">Response: 200 OK</span><br>
<span style="color:#a6e3a1;">{{"logs": [{{"id": 101, "device_id": "TC5000-A1B2C3", "time": "2026-04-23T09:02:15", "user_id": 1005, "attend_status": "CheckIn", ...}}]}}</span>
</div>

<h3>Example: Trigger Sync</h3>
<div class="api-endpoint">
<span style="color:#fab387;">curl</span> -X POST https://your-server/api/v1/sync/ \<br>
&nbsp;&nbsp;-H <span style="color:#a6e3a1;">"X-API-Key: a1b2c3d4e5f6..."</span> \<br>
&nbsp;&nbsp;-H <span style="color:#a6e3a1;">"Content-Type: application/json"</span> \<br>
&nbsp;&nbsp;-d <span style="color:#a6e3a1;">'{{"host": "TC5000-A1B2C3", "targets": ["M50-001122", "M91-AABBCC"], "mode": "merge"}}'</span><br><br>
<span style="color:#6c7086;">Response: 200 OK — includes full sync log array</span>
</div>

<h3>API Parameter Reference</h3>
<table class="params">
  <thead><tr><th>Parameter</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>employee_id</td><td>integer</td><td>Unique employee number (matches User ID on device)</td></tr>
    <tr><td>name</td><td>string</td><td>Full name (UTF-8, supports all scripts)</td></tr>
    <tr><td>department</td><td>integer</td><td>Department number (0–99)</td></tr>
    <tr><td>privilege</td><td>integer</td><td>0=User, 1=Manager, 2=Administrator</td></tr>
    <tr><td>enabled</td><td>boolean</td><td>true = can punch; false = denied on all devices</td></tr>
    <tr><td>card</td><td>string</td><td>Card / RFID number (hex or decimal)</td></tr>
    <tr><td>password</td><td>string</td><td>Door password</td></tr>
    <tr><td>timeset_1–5</td><td>integer</td><td>Access timezone slot numbers (-1 = not set)</td></tr>
    <tr><td>period_start / period_end</td><td>date (YYYY-MM-DD)</td><td>Validity window — device denies outside range</td></tr>
    <tr><td>mode (sync)</td><td>string</td><td>"merge" | "mirror" | "bidirectional"</td></tr>
  </tbody>
</table>

<div class="alert-success">
  <b>&#10003; Integration examples:</b> HR software can POST new hires on their first day. Payroll can GET logs for the month. Security systems can PUT employee.enabled=false on termination — all devices update within seconds.
</div>
"""

def appendix():
    return """
<h2>Appendix — Quick Reference</h2>

<h3>Key URLs</h3>
<table class="tbl">
  <thead><tr><th>URL</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>/</code></td><td>Home / Dashboard</td></tr>
    <tr><td><code>/online_devices</code></td><td>Live device list</td></tr>
    <tr><td><code>/device_registry/</code></td><td>Persistent device management</td></tr>
    <tr><td><code>/zones/</code></td><td>Zone / Area management</td></tr>
    <tr><td><code>/employees/</code></td><td>Employee registry (auto-push)</td></tr>
    <tr><td><code>/sync_users/</code></td><td>Manual user sync between devices</td></tr>
    <tr><td><code>/interlock/</code></td><td>Interlock configuration &amp; events</td></tr>
    <tr><td><code>/device_connection_logs/</code></td><td>Connect/disconnect log</td></tr>
    <tr><td><code>/search_attend_logs</code></td><td>Attendance log viewer &amp; filter</td></tr>
    <tr><td><code>/logs/download_csv/</code></td><td>Export attendance logs as CSV</td></tr>
    <tr><td><code>/api_keys/</code></td><td>REST API key management</td></tr>
    <tr><td><code>/api/v1/employees/</code></td><td>REST API — employee CRUD</td></tr>
    <tr><td><code>/api/v1/logs/</code></td><td>REST API — log query</td></tr>
    <tr><td><code>/api/v1/devices/</code></td><td>REST API — online device list</td></tr>
    <tr><td><code>/api/v1/sync/</code></td><td>REST API — trigger sync</td></tr>
    <tr><td><code>/control_device/&lt;id&gt;/restart/</code></td><td>Restart device (AJAX)</td></tr>
    <tr><td><code>/control_device/&lt;id&gt;/bulk_download_logs/</code></td><td>Bulk log download with date range</td></tr>
  </tbody>
</table>

<h3>Troubleshooting</h3>
<table class="tbl">
  <thead><tr><th>Problem</th><th>Likely Cause</th><th>Fix</th></tr></thead>
  <tbody>
    <tr><td>Device not appearing in Online Devices</td><td>Wrong server URL on device, or broker not running</td><td>Check broker is running; verify device server URL setting</td></tr>
    <tr><td>Login rejected (token invalid)</td><td>Token mismatch or device not in registry</td><td>Go to Device Registry, find/add device, reset token if needed</td></tr>
    <tr><td>Sync fails with "Host not found"</td><td>Host device offline</td><td>Ensure host device is in Online Devices list before syncing</td></tr>
    <tr><td>Employee push fails silently</td><td>No devices online</td><td>Check Online Devices — at least one must be connected</td></tr>
    <tr><td>Interlock not triggering</td><td>Device not in DeviceRegistry with interlock_enabled=True</td><td>Go to Device Registry → Edit → Enable Interlock</td></tr>
    <tr><td>API returns 401 Unauthorized</td><td>Missing or invalid API key</td><td>Generate key at /api_keys/ and pass as X-API-Key header</td></tr>
    <tr><td>CSV export empty</td><td>No logs match the filters</td><td>Check date range and device_id parameters</td></tr>
  </tbody>
</table>
"""

# ── Assemble & render ─────────────────────────────────────────────────────────

def build_html():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{CSS_STR}</style>
</head>
<body>
{cover()}
{toc()}
{sec1()}
{sec2()}
{sec3()}
{sec4()}
{sec5()}
{sec6()}
{sec7()}
{sec8()}
{sec9()}
{sec10()}
{sec11()}
{sec12()}
{sec13()}
{sec14()}
{sec15()}
{sec16()}
{sec17()}
{sec18()}
{sec19()}
{sec20()}
{sec21()}
{sec22()}
{sec23()}
{appendix()}
</body>
</html>"""

if __name__ == "__main__":
    out = "/run/media/batman/BatMan/WebSocketSDK_Python/UserManual.pdf"
    print("Building HTML...")
    html = build_html()

    print("Rendering PDF with WeasyPrint...")
    HTML(string=html, base_url=".").write_pdf(out)
    size_mb = os.path.getsize(out) / 1_048_576
    print(f"✓ PDF written: {out}  ({size_mb:.1f} MB)")
