"""Institution dashboard: upload, validate, score, review and download."""
import logging
import altair as alt
import pandas as pd
import streamlit as st
from common import DATA_NOTE, DISCLAIMER, feedback_box, get_bundle
from investor_app import AVERAGE_RATE, MAX_UPLOAD_ROWS, SAMPLE_PATH, likelihood_band, prepare_rows, score_customers, template_columns, template_csv, validate_upload
from styles import apply_styles, hero, process_strip

logger=logging.getLogger(__name__); bundle=get_bundle(); choices=bundle["form_choices"]
BAND_ORDER=["High","Medium","Low"]
BAND_MEANING={"High":"8% or more: about 3 times the average or more. Review these profiles first.","Medium":"3% to 8%: around or a little above the average.","Low":"Below 3%: below the average."}
def read_customer_csv(source): return pd.read_csv(source,keep_default_na=False,na_values=[""])

apply_styles()
hero("Institution dashboard","Prioritise customer profiles with explainable investor likelihood","Upload a validated CSV, review High, Medium and Low likelihood bands, inspect model reasons and download a ranked list.")
process_strip([("Upload","Provide the 11 approved inputs or use sample data."),("Validate and score","Invalid records are separated before scoring."),("Prioritise","Review bands, explanations and fairness monitoring.")])
st.info("Use non-identifying customer references. Do not upload names, ID numbers, account numbers, phone numbers or email addresses.")

left,right=st.columns([2,1],gap="large")
with left:
    st.markdown("### Upload customer data")
    uploaded=st.file_uploader("Customer CSV",type="csv",help=f"Maximum {MAX_UPLOAD_ROWS:,} rows per upload.")
with right:
    st.markdown("### Start safely")
    try: st.download_button("Download CSV template",template_csv(bundle),"customer_list_template.csv","text/csv",use_container_width=True)
    except Exception: logger.exception("Template preparation failed"); st.error("The template could not be prepared.")
    sample_clicked=st.button("Try sample data",type="primary",use_container_width=True)
with st.expander("Required columns and accepted values"):
    try: st.dataframe(template_columns(bundle),hide_index=True,use_container_width=True)
    except Exception: logger.exception("Template columns failed"); st.error("Column guidance is temporarily unavailable.")

if sample_clicked:
    try: st.session_state["inst_raw"]=read_customer_csv(SAMPLE_PATH); st.session_state["inst_source"]="sample data (held-out survey profiles)"
    except Exception: logger.exception("Sample CSV load failed"); st.error("The sample file could not be loaded.")
if uploaded is not None:
    try: st.session_state["inst_raw"]=read_customer_csv(uploaded); st.session_state["inst_source"]=uploaded.name
    except Exception: logger.exception("Uploaded CSV read failed"); st.error("We couldn't read that CSV. Use the supplied template."); st.stop()
if "inst_raw" not in st.session_state:
    st.info("Upload a customer list or use the sample data to begin."); feedback_box("institutions"); st.stop()
raw=st.session_state["inst_raw"]
if len(raw)>MAX_UPLOAD_ROWS: st.error(f"The file has {len(raw):,} rows. Upload at most {MAX_UPLOAD_ROWS:,} rows."); st.stop()
try: valid,problems,missing=validate_upload(bundle,raw)
except Exception: logger.exception("Upload validation failed"); st.error("We couldn't validate this file. Compare it with the template."); st.stop()
if missing: st.error("Missing columns: **"+", ".join(missing)+"**"); st.stop()
if len(problems):
    st.warning(f"{problems['Row in file'].nunique()} row(s) were skipped because of invalid answers.")
    with st.expander("Review invalid rows"): st.dataframe(problems,hide_index=True,use_container_width=True)
if valid.empty: st.error("No valid rows are available to score."); st.stop()
try:
    with st.spinner(f"Scoring {len(valid):,} profiles..."): results=score_customers(bundle,valid)
except Exception: logger.exception("Batch scoring failed"); st.error("We couldn't score this file. Review the inputs and try again."); st.stop()

st.success(f"Scoring complete · Source: {st.session_state['inst_source']}")
counts=results["band"].value_counts().reindex(BAND_ORDER,fill_value=0)
m1,m2,m3,m4=st.columns(4); m1.metric("Profiles scored",f"{len(results):,}"); m2.metric("High",f"{counts['High']:,}"); m3.metric("Medium",f"{counts['Medium']:,}"); m4.metric("Low",f"{counts['Low']:,}")
with st.expander("What do the bands mean?"):
    for band in BAND_ORDER: st.markdown(f"- **{band}:** {BAND_MEANING[band]}")
    st.caption(f"Investors represented {AVERAGE_RATE:.1%} of survey adults. On held-out test data, 14.3% of High, 5.0% of Medium and 0.8% of Low profiles were actual investors.")

chart_col,table_col=st.columns([1,2],gap="large")
with chart_col:
    st.subheader("Band distribution")
    chart=alt.Chart(counts.rename_axis("Band").reset_index(name="Profiles")).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(x=alt.X("Band:N",sort=BAND_ORDER,title=None),y="Profiles:Q",color=alt.Color("Band:N",scale=alt.Scale(domain=BAND_ORDER,range=["#0F766E","#E76F51","#64748B"]),legend=None),tooltip=["Band","Profiles"])
    st.altair_chart(chart,use_container_width=True)
with table_col:
    st.subheader("Ranked profiles")
    show=st.multiselect("Show bands",BAND_ORDER,default=BAND_ORDER)
    table=results[results["band"].isin(show)].rename(columns={"customer_id":"Customer","band":"Band","likelihood_pct":"Likelihood (%)","times_average":"Times average","reason_1":"Main reason","reason_2":"Second reason","reason_3":"Third reason","sex":"Sex"})
    st.dataframe(table,hide_index=True,use_container_width=True)
    st.download_button("Download ranked list",results.to_csv(index=False),"investor_likelihood_ranked.csv","text/csv",type="primary",use_container_width=True)

if "sex" in results.columns:
    with st.expander("Fairness monitoring · report by sex"):
        by_sex=(results.groupby("sex")["band"].value_counts(normalize=True).mul(100).round(1).unstack(fill_value=0).reindex(columns=BAND_ORDER,fill_value=0)); by_sex.insert(0,"People",results["sex"].value_counts())
        st.dataframe(by_sex.rename(columns=lambda c:f"{c} (%)" if c in BAND_ORDER else c),use_container_width=True)
        st.caption("Sex is not used in scoring. It is shown only for group reporting and fairness monitoring.")

st.subheader("Inspect one profile")
person_id=st.selectbox("Choose a customer reference",results["customer_id"].astype(str).tolist())
row_index=results.index[results["customer_id"].astype(str)==person_id][0]; person=results.loc[row_index]; answers=valid.loc[row_index].to_dict()
d1,d2=st.columns(2); d1.metric("Band",person["band"]); d2.metric("Likelihood",f"{person['likelihood_pct']:.1f}%",help=f"About {person['times_average']:.1f}× the survey average")
for k in (1,2,3):
    if person[f"reason_{k}"]: st.write(f"- {person[f'reason_{k}']}")
with st.expander("Explore a what-if scenario"):
    st.caption("What-if results show model sensitivity, not cause and effect.")
    w1,w2=st.columns(2); what_if=dict(answers)
    what_if["education"]=w1.selectbox("Education",choices["education"],index=choices["education"].index(answers["education"]),key="inst_wi_edu")
    missing_income=pd.isna(answers["monthly_income"]); base=0 if missing_income else int(answers["monthly_income"])
    new_income=w2.number_input("Monthly income (KSh)",0,10_000_000,base,5000,key="inst_wi_income",help="Income was not supplied" if missing_income else None)
    what_if["monthly_income"]=None if missing_income and new_income==0 else new_income
    try:
        new_prob=bundle["final_model"].predict_proba(prepare_rows(bundle,pd.DataFrame([what_if])))[:,1][0]; change=new_prob*100-person["likelihood_pct"]
        st.metric("Likelihood with changes",f"{new_prob:.1%}",f"{change:+.1f} points"); st.write(f"Band: **{likelihood_band(new_prob,bundle['settings'])}** (current: {person['band']})")
    except Exception: logger.exception("Institution what-if failed"); st.error("We couldn't complete this comparison.")

st.caption("Investor likelihood reflects similarity to current investors. It is not a measure of ability or readiness to invest.")
st.caption(DATA_NOTE); st.caption(DISCLAIMER); feedback_box("institutions")
