"""For institutions: upload a customer list (or the sample) -> likelihood bands, reasons, next steps, download."""
import logging

import altair as alt
import pandas as pd
import streamlit as st

from common import (INCOME_RANGE_TEXT, NEXT_STEP, SURVEY_INCOME_RANGE, ai_answer, footer, get_bundle,
                    llm_available, read_customer_csv)
from investor_app import (AVERAGE_RATE, MAX_UPLOAD_ROWS, SAMPLE_PATH, likelihood_band, prepare_rows,
                          score_customers, template_columns, template_csv, validate_upload)
from llm_layer import INSTITUTION_RULES, build_institution_prompt
from styles import BAND_COLORS, BAND_SOFT, band_badge, hero, note, process_strip, view_switcher

logger = logging.getLogger(__name__)
bundle = get_bundle()
choices = bundle["form_choices"]
BAND_ORDER = ["High", "Medium", "Low"]
BAND_MEANING = {
    "High": "8% or more: about 3 times the average or more.",
    "Medium": "3% to 8%: around or a little above the average.",
    "Low": "Below 3%: below the average.",
}
VIEWS = ["📊 Overview", "📋 Ranked list", "👤 One person", "⚖️ Fairness"]

hero("For institutions", "Find customers who are likely to invest",
     "Upload your customer list, or try the sample. Each person gets an investor likelihood band "
     "(High, Medium or Low), the main reasons and a suggested next step, in a list you can download.")

has_list = "inst_raw" in st.session_state
if not has_list:
    process_strip([("Upload", "Your list with the 11 columns, or the sample data."),
                   ("Check and score", "Rows with problems are set aside and listed for you."),
                   ("Act", "Start with High, nurture Medium, build basics with Low.")])
    note("info", "Privacy", "Use your own customer reference numbers. Do not upload names, ID numbers, account "
                            "numbers, phone numbers or email addresses.")

# Upload area (smaller once a list is loaded)
up_col, side_col = st.columns([2, 1], gap="large")
with up_col:
    uploaded = st.file_uploader("Upload a customer list (CSV)" if not has_list else "Upload a different list (CSV)",
                                type="csv", help=f"Up to {MAX_UPLOAD_ROWS:,} rows at a time.")
with side_col:
    st.write("")
    sample_clicked = st.button("Try with sample data", type="primary" if not has_list else "secondary",
                               use_container_width=True)
    st.download_button("Download an example file", template_csv(bundle), "customer_list_template.csv",
                       "text/csv", use_container_width=True)
with st.expander("Which columns does my file need?"):
    st.dataframe(template_columns(bundle), hide_index=True, use_container_width=True)

if sample_clicked:
    try:
        st.session_state["inst_raw"] = read_customer_csv(SAMPLE_PATH)
        st.session_state["inst_source"] = "sample data (150 people from the survey's test set)"
        st.session_state.pop("inst_view", None)
    except Exception:
        logger.exception("Sample file failed to load")
        st.error("The sample file could not be loaded. Please upload your own list for now.")
if uploaded is not None and st.session_state.get("inst_upload_id") != uploaded.file_id:
    # Read a new upload once (so pressing "Try with sample data" later still works)
    try:
        st.session_state["inst_raw"] = read_customer_csv(uploaded)
        st.session_state["inst_source"] = uploaded.name
        st.session_state["inst_upload_id"] = uploaded.file_id
        st.session_state.pop("inst_view", None)
    except Exception:
        st.error("We couldn't read that file. Please upload a comma-separated (CSV) file with a header row, "
                 "like the example file.")
        st.stop()

if "inst_raw" not in st.session_state:
    st.info("Upload a customer list or try the sample data to get started.")
    footer("institutions")
    st.stop()

# Check and score
raw = st.session_state["inst_raw"]
if len(raw) > MAX_UPLOAD_ROWS:
    st.error(f"The file has {len(raw):,} rows. Please upload at most {MAX_UPLOAD_ROWS:,} rows at a time.")
    st.stop()

valid, problems, missing = validate_upload(bundle, raw)
if missing:
    st.error("Your file is missing these columns: **" + ", ".join(missing) + "**. "
             "Open **Which columns does my file need?** for the list and an example file.")
    st.stop()
if len(problems):
    st.warning(f"{problems['Row in file'].nunique()} row(s) had answers we couldn't use and were skipped. "
               "Fix them and upload again to include them.")
    with st.expander("See the problems"):
        st.dataframe(problems, hide_index=True, use_container_width=True)
if valid.empty:
    st.error("No rows could be scored. Please check the problems above.")
    st.stop()

try:
    with st.spinner(f"Scoring {len(valid):,} people..."):
        results = score_customers(bundle, valid)
except Exception:
    logger.exception("Scoring failed")
    st.error("Sorry, something went wrong while scoring the list. Please check the file and try again.")
    st.stop()

# Incomes outside what people reported in the survey get a note
low, high = SURVEY_INCOME_RANGE
income = pd.to_numeric(valid.loc[results.index, "monthly_income"], errors="coerce")
outside = income.notna() & ((income < low) | (income > high))
results["note"] = ["Income outside the survey's range" if flag else "" for flag in outside]
counts = results["band"].value_counts().reindex(BAND_ORDER, fill_value=0)

st.success(f"Scored {len(results):,} people · Source: {st.session_state['inst_source']}")
view = view_switcher(VIEWS, "inst_view")

# ---------------------------------------------------------------------------
# Overview: tiles, chart and the next step for each band
# ---------------------------------------------------------------------------
if view == "📊 Overview":
    expected = results["likelihood_pct"].sum() / 100
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("People scored", f"{len(results):,}")
    m2.metric("High", f"{counts['High']:,}")
    m3.metric("Medium", f"{counts['Medium']:,}")
    m4.metric("Low", f"{counts['Low']:,}")
    m5.metric("Likely investors", f"about {expected:,.0f}",
              help="The sum of everyone's likelihood. Because the model is calibrated, this estimates how many "
                   "people in the list are investors today.")
    if outside.any():
        note("warn", f"{int(outside.sum())} people have an income outside the survey's range.", INCOME_RANGE_TEXT)

    chart_col, steps_col = st.columns([5, 6], gap="large")
    with chart_col:
        st.subheader("People by band")
        chart_data = counts.rename_axis("Band").reset_index(name="People")
        bars = (
            alt.Chart(chart_data)
            .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=70)
            .encode(x=alt.X("Band:N", sort=BAND_ORDER, title=None,
                            axis=alt.Axis(labelAngle=0, labelFontSize=15, labelFontWeight="bold")),
                    y=alt.Y("People:Q", title="People", axis=alt.Axis(labelFontSize=13, titleFontSize=14)),
                    color=alt.Color("Band:N", scale=alt.Scale(domain=BAND_ORDER,
                                                              range=[BAND_COLORS[b] for b in BAND_ORDER]), legend=None),
                    tooltip=["Band", "People"])
        )
        labels = bars.mark_text(dy=-10, fontSize=15, fontWeight="bold").encode(text="People:Q",
                                                                                color=alt.value("#0A1F3C"))
        st.altair_chart((bars + labels).properties(height=380), use_container_width=True)
    with steps_col:
        st.subheader("Recommended next step")
        for band in BAND_ORDER:
            st.markdown(
                f'<div class="note" style="background:{BAND_SOFT[band]};border-left:5px solid {BAND_COLORS[band]}">'
                f'{band_badge(band)} &nbsp;<strong>{counts[band]:,} people</strong> · {BAND_MEANING[band]}<br>'
                f'{NEXT_STEP[band]}</div>', unsafe_allow_html=True)
        st.caption(f"The average Kenyan adult in the survey has a {AVERAGE_RATE:.1%} chance of being an investor. "
                   "On our test data, 14.3% of High, 5.0% of Medium and 0.8% of Low people actually invested.")

# ---------------------------------------------------------------------------
# Ranked list: filter, table and download
# ---------------------------------------------------------------------------
elif view == "📋 Ranked list":
    show_bands = st.multiselect("Show bands", BAND_ORDER, default=BAND_ORDER)
    table = results[results["band"].isin(show_bands)].rename(columns={
        "customer_id": "Customer", "band": "Band", "likelihood_pct": "Likelihood (%)",
        "times_average": "Times the average", "reason_1": "Main reason", "reason_2": "Second reason",
        "reason_3": "Third reason", "sex": "Sex", "note": "Note",
    })
    st.caption(f"Showing {len(table):,} of {len(results):,} people, most likely first.")
    st.dataframe(table, hide_index=True, use_container_width=True, height=480)
    st.download_button("Download the ranked list (CSV)", results.to_csv(index=False),
                       "investor_likelihood_ranked.csv", "text/csv", type="primary")

# ---------------------------------------------------------------------------
# One person: band, reasons, next step, AI note and what if
# ---------------------------------------------------------------------------
elif view == "👤 One person":
    person_id = st.selectbox("Choose a person", results["customer_id"].astype(str).tolist())
    row_index = results.index[results["customer_id"].astype(str) == person_id][0]
    person = results.loc[row_index]
    answers = valid.loc[row_index].to_dict()

    d1, d2, d3 = st.columns(3)
    d1.markdown(f"**Band**<br>{band_badge(person['band'])}", unsafe_allow_html=True)
    d2.metric("Likelihood", f"{person['likelihood_pct']:.1f}%")
    d3.metric("Times the average", f"{person['times_average']:.1f}×")
    reasons = [person[f"reason_{k}"] for k in (1, 2, 3) if person[f"reason_{k}"]]
    st.markdown("**Main reasons**\n" + "\n".join(f"- {r}" for r in reasons))
    st.markdown(f"**Recommended next step:** {NEXT_STEP[person['band']]}")
    if person["note"]:
        note("warn", "Income outside the survey's range.", INCOME_RANGE_TEXT)

    if llm_available():
        if st.button("✨ Write a short note about this person"):
            with st.spinner("Writing..."):
                text = ai_answer(build_institution_prompt(person["band"], person["likelihood_pct"],
                                                          person["times_average"], reasons), INSTITUTION_RULES)
            if text:
                with st.container(border=True):
                    st.markdown(text)
                    st.caption("Written by AI from the band and reasons above. It can make mistakes.")
            else:
                note("info", "The AI helper is busy right now.", "The reasons and next step above cover the same "
                                                                  "information. Please try again in a minute.")

    with st.expander("What if this person's situation changed?", expanded=True):
        st.caption("This shows how the model responds. It is not cause and effect.")
        w1, w2 = st.columns(2)
        what_if = dict(answers)
        what_if["education"] = w1.selectbox("Education", choices["education"],
                                            index=choices["education"].index(answers["education"]), key="inst_wi_edu")
        income_missing = pd.isna(answers["monthly_income"])
        base_income = 0 if income_missing else int(answers["monthly_income"])
        new_income = w2.number_input("Monthly income (KSh)", min_value=0, max_value=10_000_000, value=base_income,
                                     step=5_000, key="inst_wi_income",
                                     help="Income was not given for this person" if income_missing else None)
        what_if["monthly_income"] = None if income_missing and new_income == 0 else new_income
        try:
            new_prob = bundle["final_model"].predict_proba(prepare_rows(bundle, pd.DataFrame([what_if])))[:, 1][0]
            change = new_prob * 100 - person["likelihood_pct"]
            st.metric("Likelihood with these changes", f"{new_prob:.1%}", f"{change:+.1f} points")
            st.markdown(f"Band: {band_badge(likelihood_band(new_prob, bundle['settings']))} (now: {person['band']})",
                        unsafe_allow_html=True)
        except Exception:
            logger.exception("Institution what-if failed")
            st.error("We couldn't compare these answers.")

# ---------------------------------------------------------------------------
# Fairness: report by sex (sex is never used to calculate the likelihood)
# ---------------------------------------------------------------------------
else:
    if "sex" in results:
        by_sex = (results.groupby("sex")["band"].value_counts(normalize=True).mul(100).round(1)
                  .unstack(fill_value=0).reindex(columns=BAND_ORDER, fill_value=0))
        by_sex.insert(0, "People", results["sex"].value_counts())
        st.subheader("Bands by sex")
        st.dataframe(by_sex.rename(columns=lambda c: f"{c} (%)" if c in BAND_ORDER else c), use_container_width=True)
        st.caption("Sex is never used to calculate the likelihood. It is shown only so you can check that groups "
                   "are reached fairly.")
    else:
        note("info", "No sex column in this file.",
             "Add an optional 'sex' column (Female / Male) to see the share of each group in each band. It is never "
             "used to calculate the likelihood.")
    st.markdown("**What our tests showed:** at our cut-off, the model finds the same share of investors among women "
                "and men (53% each). See **Model and fairness** in the menu for more.")

st.caption("Investor likelihood shows how closely a person resembles people who already invest. It is not a "
           "measure of whether they are able or ready to invest.")
footer("institutions")
