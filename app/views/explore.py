"""Explore the data: ask about the 2024 FinAccess survey in words, or pick groups yourself. All numbers come from
data/survey_summary.csv (group counts made in the notebook); the AI only turns a question into a query."""
import altair as alt
import pandas as pd
import streamlit as st

from common import DATA_NOTE, ROOT, ai_answer, feedback_box, llm_available
from llm_layer import DATA_QUERY_RULES, build_data_query_prompt, parse_data_query
from styles import COLORS, hero, note

SUMMARY_PATH = ROOT / "data" / "survey_summary.csv"
GROUP_LABELS = {
    "sex": "Sex", "age_group": "Age group", "urban_rural": "Urban or rural", "county": "County",
    "education": "Education", "marital_status": "Marital status", "livelihood": "Type of work",
    "income_band": "Monthly income (KSh)",
}
OPTION_LABELS = {
    "shares_bonds": "shares or bonds", "funds_mmf": "money market or other funds", "sacco": "a SACCO",
    "pension": "a pension", "chama": "a chama", "savings": "a savings account",
}
MEASURES = {"people": "Number of people", "investors": "People who invest", "option": "People who use a product"}
NONE = "(none)"
EXAMPLES = ["How many people were surveyed?", "How many women invest?",
            "Which age group invests the most?", "How many people in Nairobi use a SACCO?"]


@st.cache_data(show_spinner=False)
def load_summary(path):
    # "None" is an education answer, so only empty cells are treated as blank
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def scope_words(group, value):
    # How a filter reads inside a sentence, e.g. ("county", "Kisii") -> "in Kisii"
    return {
        "sex": f"who are {value.lower()}", "age_group": f"aged {value}", "urban_rural": f"in {value.lower()} areas",
        "county": f"in {value}", "education": f"with {value.lower()} education",
        "marital_status": f"who are {value.lower()}", "livelihood": f"whose main income is {value.lower()}",
        "income_band": f"earning {value} a month" if value != "Not given" else "who didn't give their income",
    }.get(group, f"where {group} is {value}")


def lookup(table, measure, option, group_by, filter_group, filter_value):
    """
    Rows for the query, with columns: label, people, count, w_people, w_count, hidden.
    Uses the overall row, a one-way table or a two-way table, depending on how many groups are used.
    """
    count_col = {"people": "people", "investors": "investors"}.get(measure, f"{option}_users")
    if filter_group == group_by:
        filter_group = filter_value = None
    if not group_by and not filter_group:
        rows, labels = table[table["group_1"] == "all"], ["All people"]
    elif bool(group_by) != bool(filter_group):                     # one group: a one-way table
        g = group_by or filter_group
        rows = table[(table["group_1"] == g) & (table["group_2"] == "all")]
        if filter_group:
            rows = rows[rows["value_1"] == filter_value]
        labels = rows["value_1"].tolist()
    else:                                                            # two groups: a two-way table
        straight = table[(table["group_1"] == filter_group) & (table["group_2"] == group_by)]
        if len(straight):
            rows = straight[straight["value_1"] == filter_value]
            labels = rows["value_2"].tolist()
        else:
            rows = table[(table["group_1"] == group_by) & (table["group_2"] == filter_group)]
            rows = rows[rows["value_2"] == filter_value]
            labels = rows["value_1"].tolist()
    out = pd.DataFrame({
        "label": labels, "people": rows["people"].to_numpy(), "count": rows[count_col].to_numpy(),
        "w_people": rows["w_people"].to_numpy(), "w_count": rows[f"w_{count_col}"].to_numpy(),
        "hidden": rows["hidden"].astype(str).str.lower().eq("true").to_numpy(),
    })
    out["pct"] = out["count"] / out["people"] * 100
    out["w_pct"] = out["w_count"] / out["w_people"] * 100
    return out


def set_choices(query, groups):
    # Copy a valid AI query into the choice boxes below; returns an error message or None
    if not query or "error" in query:
        return (query or {}).get("error") or "We couldn't turn that question into a query."
    measure = query.get("measure")
    option = query.get("option")
    group_by = query.get("group_by")
    flt = query.get("filter") or {}
    if measure not in MEASURES or (measure == "option" and option not in OPTION_LABELS):
        return "That question asks for something the summary doesn't hold."
    if group_by and group_by not in groups:
        return "That question splits the data in a way the summary doesn't hold."
    if flt and (flt.get("group") not in groups or flt.get("value") not in groups[flt.get("group")]):
        return "We couldn't match one of the groups in that question."
    st.session_state["ex_measure"] = measure
    st.session_state["ex_option"] = option or list(OPTION_LABELS)[0]
    st.session_state["ex_group"] = group_by or NONE
    st.session_state["ex_fgroup"] = flt.get("group") or NONE
    if flt:
        st.session_state["ex_fvalue"] = flt["value"]
    return None


hero("Explore the data", "What the 2024 FinAccess survey says",
     "Ask a question in words, or pick the groups yourself. Every number comes straight from the survey, "
     "never from the AI.")

if not SUMMARY_PATH.exists():
    note("info", "The survey summary isn't uploaded yet.",
         "Run the summary cell in notebook section 9 and upload data/survey_summary.csv to GitHub.")
    st.stop()

table = load_summary(SUMMARY_PATH)
groups = {g: sorted(table.loc[(table["group_1"] == g) & (table["group_2"] == "all"), "value_1"].astype(str).unique())
          for g in GROUP_LABELS}

# Ask in words (the AI only fills in the choices below)
if llm_available():
    st.subheader("Ask in words")
    st.caption("For example: " + " · ".join(EXAMPLES))
    with st.form("explore_ask", clear_on_submit=False):
        question = st.text_input("Your question about the survey", max_chars=300,
                                 placeholder="e.g. How many women in Nairobi invest?")
        asked = st.form_submit_button("Find the answer", type="primary")
    if asked and question.strip():
        with st.spinner("Reading your question..."):
            reply = ai_answer(build_data_query_prompt(question, groups, OPTION_LABELS), DATA_QUERY_RULES)
        problem = set_choices(parse_data_query(reply), groups) if reply else "The AI helper is busy right now."
        if problem:
            note("warn", "We couldn't answer that one automatically.",
                 problem + " Try the choices below, which can combine up to two groups.")

# What to count. It is read from what is saved, so the answer can be shown first and the boxes
# (which write to the same saved names) come after it.
st.session_state.setdefault("ex_measure", "investors")
st.session_state.setdefault("ex_option", list(OPTION_LABELS)[0])
st.session_state.setdefault("ex_group", NONE)
st.session_state.setdefault("ex_fgroup", NONE)
measure = st.session_state["ex_measure"]
option = st.session_state["ex_option"] if measure == "option" else None
group_by = None if st.session_state["ex_group"] == NONE else st.session_state["ex_group"]
filter_group = None if st.session_state["ex_fgroup"] == NONE else st.session_state["ex_fgroup"]
filter_value = None
if filter_group:
    if st.session_state.get("ex_fvalue") not in groups[filter_group]:
        st.session_state["ex_fvalue"] = groups[filter_group][0]
    filter_value = st.session_state["ex_fvalue"]
result = lookup(table, measure, option, group_by, filter_group, filter_value)

# The answer
st.subheader("The answer")
scope = f" {scope_words(filter_group, filter_value)}" if filter_group else ""
what = {"people": "people", "investors": "investors"}.get(measure, f"users of {OPTION_LABELS.get(option)}")
verb = {"investors": "invest", "option": f"use {OPTION_LABELS.get(option)}"}.get(measure)
st.caption(f"What we counted: {what}{scope}" + (f", split by {GROUP_LABELS[group_by].lower()}" if group_by else "")
           + ". Counts are people in the survey; weighted % estimates the share of all Kenyan adults.")

if result.empty:
    st.info("No people in the survey match that combination.")
elif not group_by:
    row = result.iloc[0]
    if row["hidden"]:
        note("info", "Fewer than 10 people in the survey match this.",
             "Small groups are hidden so no one can be singled out.")
    elif measure == "people":
        st.metric(f"People surveyed{scope}", f"{int(row['people']):,}")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric(f"People surveyed{scope}", f"{int(row['people']):,}")
        m2.metric(f"Who {verb}", f"{int(row['count']):,}", help=f"{row['pct']:.1f}% of the people surveyed")
        m3.metric("Weighted % of Kenyan adults", f"{row['w_pct']:.1f}%",
                  help="Uses the survey weights, so it estimates the share of all Kenyan adults.")
        st.markdown(f"Of the **{int(row['people']):,}** people surveyed{scope}, **{int(row['count']):,}** {verb} "
                    f"({row['pct']:.1f}%). Using the survey weights, that is about **{row['w_pct']:.1f}%** of "
                    f"Kenyan adults{scope}.")
else:
    shown = result.copy()
    label = GROUP_LABELS[group_by]
    hidden_count = int(shown["hidden"].sum())
    shown = shown[~shown["hidden"]]
    if measure == "people":
        table_view = pd.DataFrame({label: shown["label"], "People surveyed": shown["people"].astype(int)})
        chart_col, chart_title = "People surveyed", "People surveyed"
    else:
        table_view = pd.DataFrame({
            label: shown["label"], "People surveyed": shown["people"].astype(int),
            f"Who {verb}": shown["count"].astype(int), "% in survey": shown["pct"].round(1),
            "Weighted % of Kenyan adults": shown["w_pct"].round(1),
        })
        chart_col, chart_title = "Weighted % of Kenyan adults", f"Weighted % who {verb}"
    chart = (
        alt.Chart(table_view)
        .mark_bar(cornerRadiusEnd=6, color=COLORS["primary"])
        .encode(y=alt.Y(f"{label}:N", sort="-x", title=None, axis=alt.Axis(labelFontSize=13, labelLimit=220)),
                x=alt.X(f"{chart_col}:Q", title=chart_title),
                tooltip=list(table_view.columns))
        .properties(height=max(160, 28 * len(table_view)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(table_view.sort_values(chart_col, ascending=False), hide_index=True, use_container_width=True)
    if hidden_count:
        st.caption(f"{hidden_count} group(s) with fewer than 10 people are hidden so no one can be singled out.")

# The boxes come after the answer, so the answer is the first thing people see
st.divider()
st.subheader("Or change what to count")
c1, c2, c3 = st.columns(3)
c1.selectbox("Count", list(MEASURES), format_func=MEASURES.get, key="ex_measure")
if measure == "option":
    c1.selectbox("Product", list(OPTION_LABELS), format_func=lambda k: OPTION_LABELS[k].capitalize(),
                 key="ex_option")
c2.selectbox("Split by", [NONE] + list(GROUP_LABELS), format_func=lambda g: GROUP_LABELS.get(g, g), key="ex_group")
c3.selectbox("Only include", [NONE] + list(GROUP_LABELS), format_func=lambda g: GROUP_LABELS.get(g, g),
             key="ex_fgroup")
if filter_group:
    c3.selectbox("Which", groups[filter_group], key="ex_fvalue")

st.caption("Survey answers are self-reported. Groups with fewer than 10 people are hidden. "
           "A question can combine at most two groups, for example sex and county.")
st.caption(DATA_NOTE)
feedback_box("explore")
