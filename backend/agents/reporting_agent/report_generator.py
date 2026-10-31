from __future__ import annotations

from typing import Any, Dict, Optional

import config
from utils.logger import get_logger

log = get_logger("report_generator")

DISCLAIMER = "Illustrative diagnosis from synthetic/simulated telemetry. Recommendations are advisory and require administrator verification."


def to_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# Incident Report {report['incident_id']}",
        f"**Severity:** {report['severity'].upper()}  |  **Probable root cause:** {report['probable_root_cause']}  |  **Evidence score:** {report['confidence']:.2f}",
        "",
        report["summary"],
        "",
    ]
    if report.get("key_metrics"):
        lines += ["## Key metrics" + (f" ({report['root_device']})" if report.get("root_device") else "")]
        lines += [f"- {k}: {v}" for k, v in report["key_metrics"].items()]
        lines.append("")
    if report["affected_devices"]:
        lines += ["## Affected devices"] + [f"- {d}" for d in report["affected_devices"]] + [""]
    lines += ["## Evidence"] + [f"- {e}" for e in report["evidence"]] + [""]
    lines += ["## Recommended actions"] + [f"{i}. {a}" for i, a in enumerate(report["recommended_actions"], 1)] + [""]
    if report.get("alternatives"):
        lines += ["## Alternative explanations considered"] + [f"- {a['cause']} (score {a['score']:.2f})" for a in report["alternatives"]] + [""]
    if report.get("limitations"):
        lines += ["## Limitations"] + [f"- {l}" for l in report["limitations"]] + [""]
    if report.get("ai_summary"):
        lines += ["## AI-written plain-language summary", report["ai_summary"], ""]
    lines.append(f"_{report['disclaimer']}_")
    return "\n".join(lines)


def gemini_summary(report: Dict[str, Any]) -> Optional[str]:
    """Optional: ask Gemini to rephrase the (already computed) diagnosis for non-experts.
    The model is told not to add facts. Returns None on any failure (the report still works)."""
    if not config.GEMINI_API_KEY:
        return None
    try:
        import requests

        prompt = (
            "Rewrite the following network incident diagnosis as a short plain-language summary (max 90 words) "
            "for a college IT administrator. Use ONLY the facts given; do not invent causes, devices or numbers.\n\n"
            f"Root cause: {report['probable_root_cause']}\nRoot device: {report.get('root_device')}\n"
            f"Evidence: {report['evidence']}\nActions: {report['recommended_actions']}"
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
        r = requests.post(url, headers={"x-goog-api-key": config.GEMINI_API_KEY, "Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as exc:  # network, quota, bad model name, parse error...
        log.warning("Gemini summary skipped: %s", exc)
        return None
