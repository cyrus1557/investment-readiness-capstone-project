"""LLM layer (notebook section 9.3): the LLM explains, it does not decide.

- Prompt rules and build_individual_prompt() follow the team's notebook (9.3).
- ask_llm() tries each provider in order (Groq, then Gemini by default), retries short busy errors,
  and raises LLMUnavailable if none answers, so the app can fall back to its own plain sentences.
- No Streamlit here and no API keys in code: the keys come from Streamlit secrets (see common.py).
"""
import json
import time

import pandas as pd
import requests

DISCLAIMER_LINE = ("For learning only, not personal financial advice. "
                   "Confirm product terms and provider licensing before acting.")

SYSTEM_RULES = f"""You are a friendly financial education assistant helping Kenyan adults understand
saving and investment options. Rules:
1. Only discuss products provided in the supplied information.
2. Use simple, clear and friendly language suitable for someone new to investing. Short paragraphs or bullets.
3. Explain risk, typical minimum, how easy it is to get money out, and time horizon when relevant.
4. Never recommend gambling, betting, crypto schemes or unregulated schemes.
5. Never describe someone as "not ready" or judge them.
6. Do not make up product details, amounts, minimums, returns, interest rates or guarantees.
   If a detail is not in the supplied information, say "check with the provider".
7. Do not make investment decisions on behalf of the user.
8. Never mention or calculate an investor likelihood score for an individual.
9. Always end with this exact line: {DISCLAIMER_LINE}"""

INSTITUTION_RULES = f"""You help staff at Kenyan banks, SACCOs and fund managers understand a model result
for one customer. Rules:
1. Use only the supplied band, likelihood and reasons. Do not invent other facts about the customer.
2. Investor likelihood means how closely the customer resembles people who already invest in the 2024
   FinAccess survey. It is NOT a measure of ability, readiness or creditworthiness. Say so briefly.
3. The reasons are statistical associations, not causes.
4. Never mention sex, ethnicity or religion. Never judge the customer.
5. Suggest a respectful, practical next step for the band, in 2 to 4 short bullets.
6. Keep it under 150 words. End with this exact line: {DISCLAIMER_LINE}"""

PRODUCT_COLUMNS = ["display_name", "reason", "risk", "typical_minimum", "access", "time_horizon", "regulator"]


class LLMUnavailable(Exception):
    """No provider gave an answer (no keys, busy or an error)."""


def to_records(data, columns=None):
    # DataFrame or list of dicts -> list of plain dicts (only the allowed columns)
    if isinstance(data, pd.DataFrame):
        if columns:
            data = data[[c for c in columns if c in data.columns]]
        return data.to_dict(orient="records")
    return list(data)


def build_individual_prompt(suggestions, product_table=None):
    """
    Build an individual explanation prompt without a model score (team notebook 9.3).
    Only the person's suggested options are sent, so the AI explains exactly those and nothing else.
    (product_table is accepted for older calls but no longer sent.)
    """
    options = to_records(suggestions, PRODUCT_COLUMNS + ["plain_sentence"])
    supplied_data = {"suggested_options": options}
    return f"""
Explain these {len(options)} suggested saving and investment options to an
individual in Kenya.

Explain exactly these {len(options)} options, in the same order, one short section each.
Do not mention or add any other product.

For each option, explain why it appeared (use its "reason" and "plain_sentence"), what it generally involves,
and what the individual should understand before considering it.

Use only the supplied information. Do not add amounts, interest rates, returns or minimums
that are not written in the information. Do not calculate or mention an investment
likelihood score.

Information:
{json.dumps(supplied_data, indent=2, default=str)}
"""


def build_question_prompt(suggestions, product_table, question):
    """A follow-up question about the suggested options (e.g. 'What is a money market fund?')."""
    supplied_data = {
        "suggested_options": to_records(suggestions, PRODUCT_COLUMNS),
        "approved_product_table": to_records(product_table, PRODUCT_COLUMNS),
    }
    return f"""
Answer the user's question in under 150 words, using only the supplied information.
If the question is not about saving, investing or these products, say politely that you can
only help with these options.

User's question: {question.strip()[:300]}

Information:
{json.dumps(supplied_data, indent=2, default=str)}
"""


def build_general_question_prompt(product_table, question, history=()):
    """A general question for the 'Ask the AI' page. history: earlier (question, answer) pairs, newest last."""
    earlier = "\n".join(f"User: {q}\nAssistant: {a[:600]}" for q, a in list(history)[-3:])
    return f"""
Answer the user's question about saving and investing in Kenya in under 180 words, in simple words.
Use the approved product table where it helps. If the question is not about saving, investing or money
basics, say politely that you can only help with those topics. If you don't know, say so.

Earlier in this conversation:
{earlier or "(nothing yet)"}

User's question: {question.strip()[:300]}

Approved product table:
{json.dumps(to_records(product_table, PRODUCT_COLUMNS), indent=2, default=str)}
"""


def build_institution_prompt(band, likelihood_pct, times_average, reasons):
    """Short note for institution staff about one customer's result (no personal details are sent)."""
    supplied_data = {
        "band": band,
        "likelihood_percent": round(float(likelihood_pct), 1),
        "times_the_survey_average": round(float(times_average), 1),
        "band_meaning": {"High": "8% or more", "Medium": "3% to 8%", "Low": "below 3%"}[band],
        "top_reasons": list(reasons),
    }
    return f"""
Write a short note for a staff member about this customer's investor likelihood result:
what it means, why (from the reasons), and a suitable next step for the band.

Information:
{json.dumps(supplied_data, indent=2)}
"""


# ---------------------------------------------------------------------------
# Providers (plain web requests, so no extra libraries are needed)
# ---------------------------------------------------------------------------
BUSY_CODES = {429, 500, 502, 503, 504}


def _call_groq(prompt, system, key, model, timeout):
    body = {"model": model, "temperature": 0.3, "max_completion_tokens": 1500,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    if model.startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=body, timeout=timeout,
                      headers={"Authorization": f"Bearer {key}"})
    if r.status_code != 200:
        return r.status_code, None
    return 200, r.json()["choices"][0]["message"]["content"]


def _call_gemini(prompt, system, key, model, timeout):
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048}}
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      json=body, timeout=timeout, headers={"x-goog-api-key": key})
    if r.status_code != 200:
        return r.status_code, None
    parts = r.json()["candidates"][0]["content"]["parts"]
    return 200, "".join(p.get("text", "") for p in parts)


PROVIDERS = {"groq": _call_groq, "gemini": _call_gemini}


def ask_llm(prompt, system, config, retries=2, timeout=30):
    """
    config: {"order": ["groq", "gemini"], "groq": {"key": ..., "model": ...}, "gemini": {...}}
    Returns (text, provider_name). Raises LLMUnavailable if no provider answers.
    """
    for name in config.get("order", []):
        settings = config.get(name) or {}
        if not settings.get("key") or name not in PROVIDERS:
            continue
        for attempt in range(retries + 1):
            try:
                status, text = PROVIDERS[name](prompt, system, settings["key"], settings["model"], timeout)
            except (requests.RequestException, KeyError, IndexError, ValueError):
                status, text = 503, None
            if status == 200 and text and text.strip():
                text = text.strip()
                if DISCLAIMER_LINE not in text:
                    text += "\n\n" + DISCLAIMER_LINE
                return text, name
            if status not in BUSY_CODES:
                break                       # wrong key or bad request: try the next provider
            if attempt < retries:
                time.sleep(2 * (attempt + 1))   # busy: wait 2s, then 4s, then give up on this provider
    raise LLMUnavailable("No AI provider answered.")
