"""AI-generated transaction attack explanations with OpenRouter."""

import os
import re
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Path, Query

from dotenv import load_dotenv
load_dotenv()

from backend.database import db_manager

router = APIRouter(prefix="/transactions", tags=["Transaction Explanation"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def _clean_str(val: Any) -> str:
    if not val:
        return ""
    s = str(val).strip()
    if "\n" in s:
        first_line = s.split("\n")[0]
        parts = first_line.split()
        if len(parts) >= 2:
            return parts[1]
        return parts[0]
    return s


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _ensure_30_to_40_words(text: str, is_attack: bool) -> str:
    """Ensure explanation has between 30 and 40 words."""
    words = text.split()
    if 30 <= len(words) <= 40:
        return text

    if len(words) > 40:
        trimmed = " ".join(words[:37])
        if not trimmed.endswith("."):
            trimmed += "."
        return trimmed

    # If slightly under 30 words, append professional disclaimer
    addition = " Forensic analysts must verify wallet clustering, timing, and network hops before confirmation."
    extended = text.rstrip(".") + "." + addition
    ext_words = extended.split()
    if len(ext_words) > 40:
        return " ".join(ext_words[:38]).rstrip(",") + "."
    return extended


def _fallback_explanation(is_attack: bool, risk_level: str, risk_score: float, reasons: list[str]) -> str:
    evidence = reasons[0] if reasons else "the observed transaction profile"
    verdict = "ATTACK / SUSPICIOUS" if is_attack else "NOT AN ATTACK"
    base = (
        f"{verdict}: This transaction is evaluated as {risk_level.lower()} risk ({risk_score:.1f}/100) "
        f"reflecting {evidence.lower()}. While indicators warrant scrutiny, uncertainty exists and "
        "manual forensic verification is required before making an operational determination."
    )
    return _ensure_30_to_40_words(base, is_attack)


def _build_prompt(txid: str, transaction: Dict[str, Any], is_attack: bool, net_info: Optional[Dict[str, Any]] = None) -> str:
    reasons = "; ".join(transaction.get("reasons") or ["unusual transaction graph velocity"])
    net_str = f", routed via ASN {net_info['asn']} ({net_info['asn_org']}, {net_info['country']})" if net_info and net_info.get("asn") else ""
    amount_str = f"{transaction.get('input_amount', 1.0):.2f} BTC"

    return (
        f"You are an elite cyber intelligence investigator. Analyze this Bitcoin transaction: {txid}. "
        f"Metrics: Risk Score {transaction['risk_score']:.1f}/100 ({transaction['risk_level']}), "
        f"Illicit Probability {transaction['prob_illicit']:.2f}, Anomaly Score {transaction['anomaly_score']:.2f}, "
        f"Inputs: {transaction['input_count']}, Outputs: {transaction['output_count']}, Volume: {amount_str}, "
        f"Primary Evidence: {reasons}{net_str}. "
        f"Write EXACTLY one concise paragraph of 30 to 40 words (count your words carefully). "
        f"Start with '{'ATTACK / SUSPICIOUS:' if is_attack else 'NOT AN ATTACK:'}' "
        "State the exact threat behavior observed, acknowledge uncertainty, and state human verification is advised."
    )


@router.get("/{txid}/explain")
def explain_transaction(
    txid: str = Path(..., min_length=1),
    api_key: Optional[str] = Query(None, description="Optional custom OpenRouter API Key")
):
    con = db_manager.get_connection()
    try:
        # Resolve transaction or alert ID
        row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [txid]).fetchone()
        if not row:
            alert_match = con.execute("SELECT transaction_id FROM alerts WHERE alert_id = ? LIMIT 1", [txid]).fetchone()
            if alert_match and alert_match[0]:
                txid = alert_match[0]
                row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [txid]).fetchone()
            elif txid.startswith("ALERT-") or txid.startswith("ALT-"):
                clean_id = txid.split("-", 1)[1]
                row = con.execute("SELECT * FROM transactions WHERE txid = ? LIMIT 1", [clean_id]).fetchone()
                if row:
                    txid = clean_id

        if not row:
            from backend.services.ml_service import MLService
            pred_res = MLService.predict_custom_transaction({
                "txid": txid,
                "input_amount": 1.0,
                "output_amount": 0.99,
                "fee": 0.0001,
                "input_count": 1,
                "output_count": 2
            })
            data = {
                "input_amount": 1.0,
                "output_amount": 0.99,
                "fee": 0.0001,
                "input_count": 1,
                "output_count": 2,
                "label": "unknown"
            }
            risk_score = pred_res["risk_score"]
            risk_level = pred_res["risk_level"]
            prob_illicit = pred_res["classification_probability"]
            anomaly_score = pred_res["anomaly_score"]
            reasons = pred_res["reasons"]
            alert_id = f"ALERT-{txid[:12]}"
            prediction_data = {}
        else:
            columns = [description[0] for description in con.description]
            data = dict(zip(columns, row))

            # 1. Predictions
            prediction = con.execute("SELECT * FROM model_predictions WHERE txid = ? LIMIT 1", [txid]).fetchone()
            prediction_columns = [description[0] for description in con.description]
            prediction_data = dict(zip(prediction_columns, prediction)) if prediction else {}

            prob_illicit = float(prediction_data.get("prob_illicit", 0.85 if data.get("label") == "illicit" else 0.15))
            anomaly_score = float(prediction_data.get("anomaly_score", 0.2))

            # 2. Alerts if present
            alert_row = con.execute("SELECT risk_score, risk_level, top_reason, alert_id FROM alerts WHERE transaction_id = ? OR alert_id = ? LIMIT 1", [txid, txid]).fetchone()
            if alert_row:
                risk_score = float(alert_row[0])
                risk_level = str(alert_row[1])
                reasons = [alert_row[2]] if alert_row[2] else ["anomalous transaction pattern"]
                alert_id = alert_row[3]
            else:
                risk_score = 88.0 if data.get("label") == "illicit" else (15.0 if data.get("label") == "licit" else 35.0)
                risk_level = "Critical" if risk_score >= 75 else ("High" if risk_score >= 50 else ("Medium" if risk_score >= 25 else "Low"))
                reasons = ["severe peel-chain fan-out pattern"] if risk_score >= 75 else ["standard on-chain peer transfer"]
                alert_id = f"ALERT-{txid[:12]}"

        # 3. Network Events
        net_info = None
        net_row = con.execute("SELECT src_ip, asn, asn_org, geo_country, scenario FROM network_events WHERE txid = ? LIMIT 1", [txid]).fetchone()
        if net_row:
            net_info = {
                "src_ip": _clean_str(net_row[0]),
                "asn": _clean_str(net_row[1]),
                "asn_org": _clean_str(net_row[2]),
                "country": _clean_str(net_row[3]),
                "scenario": _clean_str(net_row[4])
            }

        transaction = {
            "txid": txid,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "prob_illicit": prob_illicit,
            "anomaly_score": anomaly_score,
            "input_amount": float(data.get("input_amount", 1.0)),
            "output_amount": float(data.get("output_amount", 1.0)),
            "fee": float(data.get("fee", 0.0001)),
            "input_count": int(data.get("input_count", 1)),
            "output_count": int(data.get("output_count", 2)),
            "reasons": reasons,
        }

        is_attack = risk_score >= 50 or prob_illicit >= 0.5 or anomaly_score >= 0.7
        prompt = _build_prompt(txid, transaction, is_attack, net_info)

        # Provider credentials: query override -> env variable -> default key
        user_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None
        effective_key = user_key or os.getenv("OPENROUTER_API_KEY") or DEFAULT_API_KEY
        explanation = ""
        generated_by = "local-evidence-fallback"

        if effective_key:
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        OPENROUTER_URL,
                        headers={
                            "Authorization": f"Bearer {effective_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "http://localhost:8002",
                            "X-Title": "Bitcoin Sentinel",
                        },
                        json={
                            "model": os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.2,
                            "max_tokens": 120,
                        },
                    )
                    response.raise_for_status()
                    explanation = response.json()["choices"][0]["message"]["content"].strip()
                    generated_by = f"OpenRouter ({DEFAULT_MODEL})"
            except Exception as exc:
                print(f"[EXPLANATION ERROR] OpenRouter failed: {type(exc).__name__}: {exc}")
                if os.getenv("OPENROUTER_REQUIRED", "false").lower() == "true":
                    raise HTTPException(status_code=502, detail=f"Explanation provider failed: {exc}") from exc

        if explanation:
            explanation = _ensure_30_to_40_words(explanation, is_attack)
        else:
            explanation = _fallback_explanation(is_attack, risk_level, risk_score, reasons)

        return {
            "txid": txid,
            "alert_id": alert_id,
            "is_attack": is_attack,
            "verdict": "ATTACK / SUSPICIOUS" if is_attack else "NOT AN ATTACK (LICIT)",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "explanation": explanation,
            "word_count": _word_count(explanation),
            "generated_by": generated_by,
            "transaction_details": transaction,
            "network_details": net_info,
            "reasons": reasons,
        }
    finally:
        con.close()
