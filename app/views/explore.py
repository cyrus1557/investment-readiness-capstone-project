"""Explore the data: ask about the 2024 FinAccess survey in words, or pick groups yourself. All numbers come from
data/survey_summary.csv (group figures made in the notebook); the AI only turns a question into a query."""
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
    "income_band": "Monthly income (KSh)", "household_band": "People in the household",
    "literacy_band": "Money questions score",
}
OPTION_LABELS = {
    "shares_bonds": "shares or bonds", "funds_mmf": "money market or other funds", "sacco": "a SACCO",
    "pension": "a pension", "chama": "a chama", "savings": "a savings account",
}
# Measures that count people
COUNT_MEASURES = {"people": "Number of people", "investors": "People who invest",
                  "option": "People who use a product"}
# Measures that are a number about people: label, column, weighted column (or None), unit
NUMBER_MEASURES = {
    "age_mean": ("Average age", "age_mean", "w_age_mean", "years"),
    "age_max": ("Oldest person", "age_max", None, "years"),
    "age_min": ("Youngest person", "age_min", None, "years"),
    "income_mean": ("Average monthly income", "income_mean", "w_income_mean", "KSh"),
    "income_max": ("Highest monthly income", "income_max", None, "KSh"),
    "income_min": ("Lowest monthly income", "income_min", None, "KSh"),
    "household_mean": ("Average people in a household", "household_mean", "w_household_mean", "people"),
    "household_max": ("Largest household", "household_max", None, "people"),
    "household_min": ("Smallest household", "household_min", None, "people"),
}
MEASURES = {**COUNT_MEASURES, **{key: value[0] for key, value in NUMBER_MEASURES.items()}}
# Values that read better in their own order than alphabetically
VALUE_ORDER = {
    "age_group": ["16-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    "income_band": ["Up to 2k", "2k-5k", "5k-10k", "10k-30k", "Over 30k", "Not given"],
    "household_band": ["1", "2", "3", "4-5", "6-8", "9 or more", "Not given"],
    "literacy_band": ["None correct", "One correct", "Two correct", "All correct", "Not given"],
}
NONE = "(none)"
EXAMPLES = ["How many women in Nairobi City invest?", "What is the average income in Kisii?",
            "Which age group invests the most?", "What is the largest household?"]


@st.cache_data(show_spinner=False)
def load_summary(path):
    # "None" is an education answer, so only empty cells are treated as blank
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def group_values(table, group):
    # The values a group can take, in a sensible order
    found = table.loc[(table["group_1"] == group) & (table["group_2"] == "all"), "value_1"].astype(str)
    values = list(dict.fromkeys(found))
    order = VALUE_ORDER.get(group)
    if order and all(value in order for value in values):
        return sorted(values, key=order.index)
    return sorted(values)


def scope_words(group, value):
    # How a filter reads inside a sentence, e.g. ("county", "Kisii") -> "in Kisii"
    return {
        "sex": f"who are {value.lower()}", "age_group": f"aged {value}", "urban_rural": f"in {value.lower()} areas",
        "county": f"in {value}", "education": f"with {value.lower()} education",
        "marital_status": f"who are {value.lower()}", "livelihood": f"whose main income is {value.lower()}",
        "income_band": f"earning {value} a month" if value != "Not given" else "who didn't give their income",
        "household_band": f"in a household of {value}",
        "literacy_band": f"who got {value.lower()} on the money questions",
    }.get(group, f"where {group} is {value}")


def select_rows(table, group_by, filters):
    """
    The summary rows for this question, with a label for each row.
    The summary holds one-way and two-way tables, so at most two different groups can be used at once.
    """
    dims = []
    for group in ([group_by] if group_by else []) + [g for g, _ in filters]:
        if group not in dims:
            dims.append(group)
    if not dims:
        rows, columns = table[table["group_1"] == "all"], {}
    elif len(dims) == 1:
        group = dims[0]
        rows = table[(table["group_1"] == group) & (table["group_2"] == "all")]
        columns = {group: "value_1"}
    else:
        first, second = dims[0], dims[1]
        rows = table[(table["group_1"] == first) & (table["group_2"] == second)]
        columns = {first: "value_1", second: "value_2"}
        if rows.empty:                                   # the pair is stored the other way round
            rows = table[(table["group_1"] == second) & (table["group_2"] == first)]
            columns = {first: "value_2", second: "value_1"}
    for group, value in filters:
        rows = rows[rows[columns[group]].astype(str) == value]
    labels = rows[columns[group_by]].astype(str).tolist() if group_by else ["All people"]
    return rows, labels


def lookup(table, measure, option, group_by, filters):
    """One row per line of the answer, with the columns the page needs to show."""
    rows, labels = select_rows(table, group_by, filters)
    out = pd.DataFrame({"label": labels, "people": rows["people"].to_numpy(),
                        "hidden": rows["hidden"].astype(str).str.lower().eq("true").to_numpy()})
    if measure in COUNT_MEASURES:
        count_col = {"people": "people", "investors": "investors"}.get(measure, f"{option}_users")
        out["value"] = rows[count_col].to_numpy()
        out["pct"] = out["value"] / out["people"] * 100
        out["w_pct"] = rows[f"w_{count_col}"].to_numpy() / rows["w_people"].to_numpy() * 100
    else:
        _, column, weighted_column, _ = NUMBER_MEASURES[measure]
        out["value"] = rows[column].to_numpy()
        out["weighted"] = rows[weighted_column].to_numpy() if weighted_column else float("nan")
    return out


def show_number(measure, value):
    # A number written the way people expect for that measure
    if value is None or pd.isna(value):
        return "—"
    unit = NUMBER_MEASURES[measure][3]
    if unit == "KSh":
        return f"KSh {value:,.0f}"
    return f"{value:,.1f}" if measure.endswith("_mean") else f"{value:,.0f}"


def set_choices(query, table, valid_groups):
    """Copy a valid AI query into the boxes below. Returns an error message, or None when it worked."""
    if not query or "error" in query:
        return (query or {}).get("error") or "We couldn't turn that question into a query."
    measure, option = query.get("measure"), query.get("option")
    group_by = query.get("group_by")
    filters = [f for f in (query.get("filters") or []) if isinstance(f, dict)][:2]
    if measure not in MEASURES or (measure == "option" and option not in OPTION_LABELS):
        return "That question asks for something the survey summary doesn't hold."
    if group_by and group_by not in valid_groups:
        return "That question splits the data in a way the summary doesn't hold."
    for one in filters:
        if one.get("group") not in valid_groups or one.get("value") not in valid_groups[one.get("group")]:
            return "We couldn't match one of the groups in that question."
    used = {group_by} | {one["group"] for one in filters}
    used.discard(None)
    if len(used) > 2:
        return "That question uses more than two groups at once, which the summary can't answer."
    st.session_state["ex_measure"] = measure
    st.session_state["ex_option"] = option or list(OPTION_LABELS)[0]
    st.session_state["ex_group"] = group_by or NONE
    for slot, one in zip(("", "2"), filters + [None, None]):
        st.session_state[f"ex_fgroup{slot}"] = one["group"] if one else NONE
        if one:
            st.session_state[f"ex_fvalue{slot}"] = one["value"]
    return None


hero("Explore the data", "What the 2024 FinAccess survey says",
     "Ask a question in words, or pick the groups yourself. Every number comes straight from the survey, "
     "never from the AI.")

if not SUMMARY_PATH.exists():
    note("info", "The survey summary isn't uploaded yet.",
         "Run the summary cell in notebook section 9 and upload data/survey_summary.csv to GitHub.")
    st.stop()

table = load_summary(SUMMARY_PATH)
groups = {g: group_values(table, g) for g in GROUP_LABELS}
groups = {g: values for g, values in groups.items() if values}

# Ask in words (the AI only fills in the choices below)
ai_problem = None
if llm_available():
    st.subheader("Ask in words")
    st.caption("For example: " + " · ".join(EXAMPLES))
    with st.form("explore_ask", clear_on_submit=False):
        question = st.text_input("Your question about the survey", max_chars=300,
                                 placeholder="e.g. How many women in Nairobi City invest?")
        asked = st.form_submit_button("Find the answer", type="primary")
    if asked and question.strip():
        with st.spinner("Reading your question..."):
            reply = ai_answer(build_data_query_prompt(question, MEASURES, groups, OPTION_LABELS), DATA_QUERY_RULES)
        ai_problem = (set_choices(parse_data_query(reply), table, groups) if reply
                      else "The AI helper is busy right now.")
        if ai_problem:
            note("warn", "We can't answer that one from this survey.",
                 ai_problem + " Build the question with the choices below instead, which can combine "
                 "up to two groups.")

# What to look up. It is read from what is saved, so the answer can be shown first and the boxes
# (which write to the same saved names) come after it.
st.session_state.setdefault("ex_measure", "investors")
st.session_state.setdefault("ex_option", list(OPTION_LABELS)[0])
st.session_state.setdefault("ex_group", NONE)
measure = st.session_state["ex_measure"] if st.session_state["ex_measure"] in MEASURES else "investors"
option = st.session_state["ex_option"] if measure == "option" else None
group_by = None if st.session_state["ex_group"] == NONE else st.session_state["ex_group"]
filters = []
for slot in ("", "2"):
    st.session_state.setdefault(f"ex_fgroup{slot}", NONE)
    group = st.session_state[f"ex_fgroup{slot}"]
    if group in groups:
        if st.session_state.get(f"ex_fvalue{slot}") not in groups[group]:
            st.session_state[f"ex_fvalue{slot}"] = groups[group][0]
        filters.append((group, st.session_state[f"ex_fvalue{slot}"]))

# The summary holds one-way and two-way tables, so only two different groups can be used at once
used_groups = list(dict.fromkeys(([group_by] if group_by else []) + [g for g, _ in filters]))
if len(used_groups) > 2:
    dropped = filters[-1][0]
    filters = filters[:-1]
    note("warn", "Only two groups at a time.",
         f"The survey summary holds pairs of groups, so {GROUP_LABELS[dropped]} was left out. "
         "Remove one of the other choices below to use it.")

verb = {"investors": "invest", "option": f"use {OPTION_LABELS.get(option)}"}.get(measure, "")
result = None if ai_problem else lookup(table, measure, option, group_by, filters)

# ---------------------------------------------------------------------------
# The answer comes first
# ---------------------------------------------------------------------------
if ai_problem:
    st.info("No answer is shown for that question. Pick what to look up below and the answer comes back.")
elif result.empty:
    st.subheader("The answer")
    st.info("No people in the survey match that combination.")
else:
    st.subheader("The answer")
    scope = "".join(f" {scope_words(g, v)}" for g, v in filters)
    split = f", split by {GROUP_LABELS[group_by].lower()}" if group_by else ""
    if measure in COUNT_MEASURES:
        what = {"people": "people", "investors": "investors"}.get(measure, f"users of {OPTION_LABELS.get(option)}")
        st.caption(f"What we counted: {what}{scope}{split}. Counts are people in the survey; "
                   "weighted % estimates the share of all Kenyan adults.")
    else:
        st.caption(f"What we looked up: the {MEASURES[measure].lower()} among people{scope}{split}. "
                   "It comes from the people in the survey.")

    if not group_by:
        row = result.iloc[0]
        if row["hidden"] or pd.isna(row["value"]):
            note("info", "Fewer than 10 people in the survey match this.",
                 "Small groups are hidden so no one can be singled out.")
        elif measure == "people":
            st.metric(f"People surveyed{scope}", f"{int(row['people']):,}")
        elif measure in COUNT_MEASURES:
            m1, m2, m3 = st.columns(3)
            m1.metric(f"People surveyed{scope}", f"{int(row['people']):,}")
            m2.metric(f"Who {verb}", f"{int(row['value']):,}", help=f"{row['pct']:.1f}% of the people surveyed")
            m3.metric("Weighted % of Kenyan adults", f"{row['w_pct']:.1f}%",
                      help="Uses the survey weights, so it estimates the share of all Kenyan adults.")
            st.markdown(f"Of the **{int(row['people']):,}** people surveyed{scope}, **{int(row['value']):,}** "
                        f"{verb} ({row['pct']:.1f}%). Using the survey weights, that is about "
                        f"**{row['w_pct']:.1f}%** of Kenyan adults{scope}.")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric(MEASURES[measure], show_number(measure, row["value"]))
            m2.metric("People surveyed", f"{int(row['people']):,}")
            if not pd.isna(row["weighted"]):
                m3.metric("Weighted average", show_number(measure, row["weighted"]),
                          help="Uses the survey weights, so it estimates the figure for all Kenyan adults.")
            st.markdown(f"Among the **{int(row['people']):,}** people surveyed{scope}, the "
                        f"{MEASURES[measure].lower()} is **{show_number(measure, row['value'])}**.")
    else:
        shown = result[(~result["hidden"]) & result["value"].notna()].copy()
        hidden_count = len(result) - len(shown)
        label = GROUP_LABELS[group_by]
        if measure == "people":
            view = pd.DataFrame({label: shown["label"], "People surveyed": shown["people"].astype(int)})
            chart_col, chart_title = "People surveyed", "People surveyed"
        elif measure in COUNT_MEASURES:
            view = pd.DataFrame({
                label: shown["label"], "People surveyed": shown["people"].astype(int),
                f"Who {verb}": shown["value"].astype(int), "% in survey": shown["pct"].round(1),
                "Weighted % of Kenyan adults": shown["w_pct"].round(1),
            })
            chart_col, chart_title = "Weighted % of Kenyan adults", f"Weighted % who {verb}"
        else:
            view = pd.DataFrame({label: shown["label"], MEASURES[measure]: shown["value"].round(1),
                                 "People surveyed": shown["people"].astype(int)})
            chart_col, chart_title = MEASURES[measure], f"{MEASURES[measure]} ({NUMBER_MEASURES[measure][3]})"
        if view.empty:
            st.info("Every group here has fewer than 10 people, so nothing can be shown.")
        else:
            chart = (
                alt.Chart(view)
                .mark_bar(cornerRadiusEnd=6, color=COLORS["primary"])
                .encode(y=alt.Y(f"{label}:N", sort="-x", title=None,
                                axis=alt.Axis(labelFontSize=13, labelLimit=220)),
                        x=alt.X(f"{chart_col}:Q", title=chart_title), tooltip=list(view.columns))
                .properties(height=max(160, 28 * len(view)))
            )
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(view.sort_values(chart_col, ascending=False), hide_index=True, use_container_width=True)
        if hidden_count:
            st.caption(f"{hidden_count} group(s) with fewer than 10 people are hidden so no one can be singled out.")

# ---------------------------------------------------------------------------
# The boxes come after the answer, so the answer is the first thing people see
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Or change what to look up")
c1, c2 = st.columns(2)
c1.selectbox("Show", list(MEASURES), format_func=MEASURES.get, key="ex_measure")
if measure == "option":
    c1.selectbox("Product", list(OPTION_LABELS), format_func=lambda k: OPTION_LABELS[k].capitalize(),
                 key="ex_option")
c2.selectbox("Split by", [NONE] + list(groups), format_func=lambda g: GROUP_LABELS.get(g, g), key="ex_group")

st.caption("You can narrow the answer by up to two groups in total, counting the split above.")
f1, f2 = st.columns(2)
for column, slot, title in ((f1, "", "Only include"), (f2, "2", "And also")):
    column.selectbox(title, [NONE] + list(groups), format_func=lambda g: GROUP_LABELS.get(g, g),
                     key=f"ex_fgroup{slot}")
    if st.session_state[f"ex_fgroup{slot}"] in groups:
        column.selectbox("Which", groups[st.session_state[f"ex_fgroup{slot}"]], key=f"ex_fvalue{slot}",
                         label_visibility="collapsed")

st.caption("Survey answers are self-reported. Groups with fewer than 10 people are hidden. The summary holds "
           "counts, averages, highest and lowest only, for the groups listed above.")
st.caption(DATA_NOTE)
feedback_box("explore")
