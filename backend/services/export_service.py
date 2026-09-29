"""
Investigation Report & Export Service.
Generates comprehensive forensic investigation dossiers formatted in JSON, CSV, and HTML/PDF.
"""

import io
import csv
import json
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from backend.services.alert_service import AlertService

logger = logging.getLogger(__name__)

class ExportService:
    """Exports forensic alert reports and transaction audit logs."""

    @staticmethod
    def export_alerts_csv(alerts: List[Dict[str, Any]]) -> str:
        """Serializes alert records to CSV string."""
        if not alerts:
            return "alert_id,entity_id,transaction_id,risk_score,risk_level,top_reason,timestamp\n"
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "alert_id", "entity_id", "transaction_id", "risk_score", "risk_level",
            "classification_probability", "anomaly_score", "top_reason", "status", "timestamp"
        ], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(alerts)
        return output.getvalue()

    @staticmethod
    def export_alerts_json(alerts: List[Dict[str, Any]]) -> str:
        """Serializes alert records to JSON string."""
        return json.dumps(alerts, indent=2)

    @staticmethod
    def export_alert_dossier_html(alert_detail: Dict[str, Any]) -> str:
        """Renders a standalone, high-contrast dark investigation dossier HTML document."""
        aid = alert_detail.get("alert_id", "ALT-UNKNOWN")
        txid = alert_detail.get("transaction_id", "")
        score = alert_detail.get("risk_score", 0.0)
        level = alert_detail.get("risk_level", "Low")
        prob = alert_detail.get("classification_probability", 0.0)
        anom = alert_detail.get("anomaly_score", 0.0)
        reasons = alert_detail.get("top_reasons", [])
        shap_items = alert_detail.get("shap_contributions", [])
        tx_info = alert_detail.get("transaction_details", {})
        net_items = alert_detail.get("network_details", [])

        # Color based on level
        badge_color = "#ef4444" if level == "Critical" else ("#f59e0b" if level == "High" else ("#3b82f6" if level == "Medium" else "#10b981"))

        reasons_html = "".join([f"<li style='margin-bottom: 8px;'>{r}</li>" for r in reasons])
        
        shap_rows = "".join([
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #1e293b;'>{item.get('feature')}</td>"
            f"<td style='padding: 8px; border-bottom: 1px solid #1e293b; color: #38bdf8;'>{item.get('shap_value')}</td>"
            f"<td style='padding: 8px; border-bottom: 1px solid #1e293b;'>{item.get('feature_value')}</td></tr>"
            for item in shap_items
        ])

        net_rows = "".join([
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #1e293b;'>{n.get('src_ip')}</td>"
            f"<td style='padding: 8px; border-bottom: 1px solid #1e293b;'>{n.get('geo_country')}</td>"
            f"<td style='padding: 8px; border-bottom: 1px solid #1e293b;'>{n.get('asn')}</td>"
            f"<td style='padding: 8px; border-bottom: 1px solid #1e293b;'>{n.get('scenario')}</td></tr>"
            for n in net_items[:10]
        ])

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Forensic Investigation Dossier — {aid}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
  .card {{ background-color: #1e293b; border-radius: 8px; padding: 24px; margin-bottom: 24px; border: 1px solid #334155; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }}
  .badge {{ background-color: {badge_color}; color: #ffffff; padding: 4px 12px; border-radius: 9999px; font-weight: bold; text-transform: uppercase; font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
  .stat {{ background-color: #0f172a; padding: 16px; border-radius: 6px; border: 1px solid #334155; }}
  .stat-label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
  .stat-value {{ font-size: 24px; font-weight: bold; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
  th {{ background-color: #0f172a; padding: 10px 8px; border-bottom: 2px solid #334155; color: #94a3b8; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1 style="margin:0; font-size: 24px; color: #38bdf8;">CYBER INVESTIGATION DOSSIER</h1>
      <p style="margin: 4px 0 0 0; color: #94a3b8;">Alert Reference: {aid} | Target: {txid}</p>
    </div>
    <span class="badge">{level} SEVERITY</span>
  </div>

  <div class="grid">
    <div class="stat"><div class="stat-label">Composite Risk Score</div><div class="stat-value" style="color: {badge_color};">{score}/100</div></div>
    <div class="stat"><div class="stat-label">ML Illicit Probability</div><div class="stat-value">{int(prob*100)}%</div></div>
    <div class="stat"><div class="stat-label">Isolation Anomaly Score</div><div class="stat-value">{int(anom*100)}%</div></div>
    <div class="stat"><div class="stat-label">Time Step / Block Epoch</div><div class="stat-value">TS {tx_info.get('time_step', 1)}</div></div>
  </div>

  <div class="card">
    <h3 style="margin-top:0; color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 8px;">Forensic Evidence & Decision Rationales</h3>
    <ul style="color: #cbd5e1; padding-left: 20px; line-height: 1.6;">
      {reasons_html}
    </ul>
  </div>

  <div class="card">
    <h3 style="margin-top:0; color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 8px;">Top SHAP Feature Attributions (Local Explainability)</h3>
    <table>
      <thead>
        <tr><th>Feature Name</th><th>SHAP Value</th><th>Observed Feature Value</th></tr>
      </thead>
      <tbody>
        {shap_rows}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h3 style="margin-top:0; color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 8px;">Correlated Network Telemetry</h3>
    <table>
      <thead>
        <tr><th>Source IP</th><th>Country</th><th>ASN</th><th>Scenario Signature</th></tr>
      </thead>
      <tbody>
        {net_rows if net_rows else "<tr><td colspan='4' style='padding:8px;'>No network telemetry recorded.</td></tr>"}
      </tbody>
    </table>
  </div>

  <p style="text-align:center; color: #64748b; font-size: 12px; margin-top: 40px;">
    Confidential Investigative Material — Generated by AI-Powered Bitcoin Transaction Monitoring Platform (NTRO 26146)
  </p>
</body>
</html>"""
        return html
