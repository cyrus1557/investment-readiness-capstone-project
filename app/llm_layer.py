"""LLM layer (notebook section 9.3): the LLM explains, it does not decide.

- Prompt rules and build_individual_prompt() follow the team's notebook (9.3).
- ask_llm() tries each provider in order (Groq, then Gemini by default), retries short busy errors,
  and raises LLMUnavailable if none answers, so the app can fall back to its own plain sentences.
- No Streamlit here and no API keys in code: the keys come from Streamlit secrets (see common.py).
"""
import json
import re
import time

import pandas as pd
import requests

DISCLAIMER_LINE = ("For learning only, not personal financial advice. "
                   "Confirm product terms and provider licensing before acting.")

SYSTEM_RULES = """You are a friendly financial education assistant helping Kenyan adults understand
saving and investing. Rules:
1. Use simple, friendly language for someone new to investing. Short bullets, each about 15 words or fewer.
2. Format with Markdown: short headings, bold labels and bullet points. No long paragraphs.
3. You may explain in general terms what a product is, how it works and why it suits someone at that stage.
4. Never invent figures. Do not give amounts, minimums, fees, interest rates or returns unless they are
   in the supplied information. Rates and rules change, so say where to check instead.
5. Never recommend gambling, betting, crypto schemes or unregulated schemes.
6. Never describe someone as "not ready" or judge them.
7. Do not make investment decisions on behalf of the user or tell them what to buy.
8. Never mention or calculate an investor likelihood score for an individual.
9. Never mention internal field names such as "reason", "plain_sentence" or "display_name".
10. Do not write any links or web addresses yourself.
11. Do not write a disclaimer. The app adds one."""

INSTITUTION_RULES = """You help staff at Kenyan banks, SACCOs and fund managers understand a model result
for one customer. Rules:
1. Use only the supplied band, likelihood and reasons. Do not invent other facts about the customer.
2. Investor likelihood means how closely the customer resembles people who already invest in the 2024
   FinAccess survey. It is NOT a measure of ability, readiness or creditworthiness. Say so briefly.
3. The reasons are statistical associations, not causes.
4. Never mention sex, ethnicity or religion. Never judge the customer.
5. Suggest a respectful, practical next step for the band, in 2 to 4 short bullets.
6. Keep it under 150 words. Use Markdown bullets with bold labels.
7. Do not write a disclaimer. The app adds one."""

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


REASON_MEANING = {
    "Starter option": "Few people with answers like this person's use investment products yet, so this is a "
                      "simple, lower-risk first step that many similar people already use.",
    "Common among similar people": "Many people in the survey with similar age, income, work and location "
                                   "already use this.",
    "Next step": "People like this person use this more often than the average Kenyan adult, so it is a "
                 "natural step up once the basics are in place.",
}


def build_individual_prompt(suggestions, product_table=None):
    """
    Build an individual explanation prompt without a model score (team notebook 9.3).
    Only the person's suggested options are sent, so the AI explains exactly those and nothing else.
    (product_table is accepted for older calls but no longer sent.)
    """
    options = to_records(suggestions, PRODUCT_COLUMNS + ["plain_sentence"])
    for option in options:
        option["what_the_reason_means"] = REASON_MEANING.get(option.get("reason"), "")
    supplied_data = {"suggested_options": options}
    return f"""
Explain these {len(options)} suggested saving and investment options to a person in Kenya.
Explain exactly these {len(options)} options, in the same order. Do not mention any other product.
Only use product details from the information below.

Use exactly this layout for each option:

### <number>. <option name>
**Why it's suggested**
- 1 or 2 bullets that explain the reason in your own words, using what_the_reason_means and how many
  people like them use it. Explain WHY, don't just repeat the words.

**What it is**
- 1 or 2 bullets: what it is and how it works, in everyday words.

**Good to know**
- **Risk:** ...
- **Getting your money out:** ...
- **Time horizon:** ...
- **Minimum:** ...
- **Regulator:** ...

After the last option, add:

### Before you choose
- 2 or 3 short, practical tips that fit these options.

Keep every bullet short (about 15 words or fewer). Speak to the person as "you".
No figures that are not in the information below.

Information:
{json.dumps(supplied_data, indent=2, default=str)}
"""


# Trusted sources the AI may point to (it picks the ids; the app writes the real links, so no made-up links)
SOURCES = {
    "cbk": ("Central Bank of Kenya", "https://www.centralbank.go.ke/"),
    "cbk_securities": ("CBK: Treasury bills and bonds", "https://www.centralbank.go.ke/securities/"),
    "cbk_tbills": ("CBK: How Treasury bills work", "https://www.centralbank.go.ke/securities/treasury-bills/"),
    "cma": ("Capital Markets Authority (shares, unit trusts, fund managers)", "https://www.cma.or.ke/"),
    "cma_guide": ("CMA: Beginner's guide to investing",
                  "https://cma.or.ke/wp-content/uploads/2023/03/CMA-Beginners-guide.pdf"),
    "cma_faq": ("CMA: Shares, bonds and CDS accounts (FAQ)",
                "https://www.cma.or.ke/download/15/brochures/3733/frequently-asked-questions.pdf"),
    "sasra": ("SASRA: the SACCO regulator", "https://www.sasra.go.ke/"),
    "rba": ("Retirement Benefits Authority", "https://www.rba.go.ke/"),
    "rba_ipp": ("RBA: Individual pension plans",
                "https://www.rba.go.ke/saving-for-retirement-through-a-registered-individual-pension-plan/"),
    "ira": ("Insurance Regulatory Authority", "https://ira.go.ke/"),
    "finaccess": ("FSD Kenya: 2024 FinAccess key insights",
                  "https://www.fsdkenya.org/blogs-publications/"
                  "2024-finaccess-household-survey-key-insights-into-kenyas-financial-landscape/"),
}
# If the AI names no source, pick one from words in the question (so there is always at least one)
SOURCE_KEYWORDS = [
    ("sacco", "sasra"), ("pension", "rba_ipp"), ("retire", "rba_ipp"), ("treasury bill", "cbk_tbills"),
    ("t-bill", "cbk_tbills"), ("bond", "cbk_securities"), ("share", "cma_faq"), ("stock", "cma_faq"),
    ("nse", "cma_faq"), ("cds", "cma_faq"), ("money market", "cma"), ("unit trust", "cma"), ("fund", "cma"),
    ("insur", "ira"), ("bank", "cbk"), ("invest", "cma_guide"),
]
QUESTION_MARKER = "[QUESTION]"
QUESTION_DISCLAIMER = ("This answer was written by AI from general knowledge. It may be wrong or out of date, "
                       "and it isn't financial advice. Check the sources above or a licensed provider before acting.")


def _question_prompt(question, product_table, suggestions=None, history=()):
    earlier = "\n".join(f"User: {q}\nAssistant: {a[:500]}" for q, a in list(history)[-3:])
    options = to_records(suggestions, PRODUCT_COLUMNS) if suggestions is not None else []
    source_list = "\n".join(f"- {key}: {title}" for key, (title, _) in SOURCES.items())
    return f"""{QUESTION_MARKER}
Answer the user's question about saving, investing or money in Kenya, using general, well-known knowledge.
If the question is not about money, saving or investing, politely say you can only help with those topics.

Use this layout (under 180 words in total):
- Start with a direct 1 or 2 sentence answer to the question.
- **How it works**: 2 to 4 short bullets.
- **Good to know**: 1 to 3 short bullets (risks, who regulates it, what to check).
- Only if it relates to the person's suggested options below, add **How it relates to your options**: 1 bullet.

Do not give exact current figures such as rates, prices, minimums or fees; say where to check instead.

On the very last line, write SOURCES: followed by 1 to 3 ids from this list that best help the user
read more, separated by commas (for example: SOURCES: sasra, finaccess).
If the message is a greeting, a thank-you, or off-topic and you decline it, write exactly: SOURCES: none
Use only these ids:
{source_list}

The person's suggested options (may be empty): {json.dumps(options, default=str)}
Approved product table (use where it helps): {json.dumps(to_records(product_table, PRODUCT_COLUMNS), default=str)}

Earlier in this conversation:
{earlier or "(nothing yet)"}

User's question: {question.strip()[:300]}
"""


def build_question_prompt(suggestions, product_table, question):
    """The 'Ask a question' box on the results page (knows the person's options)."""
    return _question_prompt(question, product_table, suggestions=suggestions)


def build_general_question_prompt(product_table, question, history=()):
    """The 'Ask the AI' page. history: earlier (question, answer) pairs, newest last."""
    return _question_prompt(question, product_table, history=history)


def _finish_question(text, prompt):
    # Take the SOURCES line off, keep only known ids (1 to 3), and add real links plus the question disclaimer
    lines, chosen, said_none = [], [], False
    for line in text.strip().splitlines():
        found = re.match(r"^\W*sources\W*:(.*)$", line.strip(), flags=re.IGNORECASE)
        if found:
            said_none = said_none or "none" in found.group(1).lower()
            chosen += [k for k in re.findall(r"[a-z_]+", found.group(1).lower()) if k in SOURCES]
        else:
            lines.append(line)
    body = "\n".join(lines).rstrip()
    body = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", body)      # drop any links the AI wrote
    if said_none and not chosen:
        return body                     # greeting or off-topic: no links and no disclaimer needed
    if not chosen:
        lowered = prompt.rsplit("User's question:", 1)[-1].lower()
        chosen = [key for word, key in SOURCE_KEYWORDS if word in lowered][:1] or ["finaccess"]
    chosen = list(dict.fromkeys(chosen))[:3]
    links = "\n".join(f"- [{SOURCES[k][0]}]({SOURCES[k][1]})" for k in chosen)
    return f"{body}\n\n**📚 Read more**\n{links}\n\n> ⚠️ **Disclaimer:** {QUESTION_DISCLAIMER}"


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
# Explore the data: the AI only turns a question into a small query; our code does all the counting
# ---------------------------------------------------------------------------
DATA_QUERY_MARKER = "[DATA_QUERY]"
DATA_QUERY_RULES = ("You turn questions about a survey into a small JSON query. Reply with JSON only: "
                    "no other words, no code fences.")


def build_data_query_prompt(question, groups, options):
    """groups: {group name: [allowed values]}; options: {product key: product name}."""
    return f"""{DATA_QUERY_MARKER}
Turn the user's question into a JSON query over a summary of the 2024 FinAccess survey of Kenyan adults.

JSON keys:
- "measure": "people" (how many people), "investors" (people who invest in shares, bonds, Treasury bills
  or funds), or "option" (people who use one of the products below)
- "option": one of {json.dumps(list(options))} when measure is "option", otherwise null
- "group_by": one group name to split the answer by, or null
- "filter": {{"group": <group name>, "value": <exact value>}}, or null

Use at most one filter and one group_by. If the question names two characteristics (for example
"women in Nairobi"), use one as the filter and the other as group_by.
Use group names and values exactly as listed (for example: women -> "Female", Nairobi -> "Nairobi City",
young people -> group_by "age_group").
Groups and their values: {json.dumps(groups)}
Products: {json.dumps(options)}

If the question can't be answered from these groups and products, reply {{"error": "<short reason>"}}.

Question: {question.strip()[:300]}
"""


def parse_data_query(text):
    # Pull the JSON object out of the AI's reply (or None if there isn't one)
    found = re.search(r"\{.*\}", text or "", flags=re.DOTALL)
    if not found:
        return None
    try:
        return json.loads(found.group(0))
    except ValueError:
        return None


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


def with_disclaimer(text):
    # Remove any disclaimer the AI wrote itself, then add ours as a clearly marked box at the end
    lines = [line for line in text.strip().splitlines() if "for learning only" not in line.lower()]
    return "\n".join(lines).rstrip() + "\n\n> ⚠️ **Disclaimer:** " + DISCLAIMER_LINE


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
                if prompt.lstrip().startswith(DATA_QUERY_MARKER):
                    return text.strip(), name          # a JSON query: no links or disclaimer added
                if prompt.lstrip().startswith(QUESTION_MARKER):
                    return _finish_question(text, prompt), name
                return with_disclaimer(text), name
            if status not in BUSY_CODES:
                break                       # wrong key or bad request: try the next provider
            if attempt < retries:
                time.sleep(2 * (attempt + 1))   # busy: wait 2s, then 4s, then give up on this provider
    raise LLMUnavailable("No AI provider answered.")
