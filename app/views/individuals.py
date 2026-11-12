"""Three-step individual journey with recommendation cards and secondary what-if analysis."""
import html
import logging
import streamlit as st
from common import DATA_NOTE, DISCLAIMER, feedback_box, get_bundle
from investor_app import EXAMPLE_PEOPLE, recommend, standardise_answer
from styles import apply_styles, hero

logger = logging.getLogger(__name__)
MIN_AGE, MAX_AGE = 16, 105
MIN_HOUSEHOLD_SIZE, MAX_HOUSEHOLD_SIZE = 1, 20
MIN_MONTHLY_INCOME, MAX_MONTHLY_INCOME = 0, 10_000_000
bundle = get_bundle(); choices = bundle["form_choices"]

QUIZ = {
    "ind_q1": ("1. You put KSh 100 in a savings account that pays 10% interest a year. After one year, with no withdrawals, how much is in the account?", ["Less than KSh 110", "Exactly KSh 110", "More than KSh 110", "I don't know"], "Exactly KSh 110"),
    "ind_q2": ("2. Prices go up by 10% this year, and your savings earn 5% interest. After one year, can your savings buy more, the same, or less than today?", ["More", "The same", "Less", "I don't know"], "Less"),
    "ind_q3": ("3. Which is usually safer?", ["Putting all your money in one investment", "Spreading your money across several investments", "I don't know"], "Spreading your money across several investments"),
}
FORM_FIELDS = ["urban_rural", "county", "education", "marital_status", "livelihood", "has_id", "mobile_money"]
for k,v in {"ind_step":1,"ind_age":None,"ind_household_size":None,"ind_income":None,"ind_prefer_not":False,"ind_has_id":standardise_answer(bundle,"has_id","Yes"),"ind_mobile_money":"Yes"}.items(): st.session_state.setdefault(k,v)

def reset_results():
    st.session_state.pop("answers", None); st.session_state.pop("example_name", None)

def load_example(name):
    try:
        person=EXAMPLE_PEOPLE[name]
        st.session_state.update({"ind_age":person["age"],"ind_household_size":person["household_size"],"ind_income":person["monthly_income"],"ind_prefer_not":False,"ind_step":3})
        for field in FORM_FIELDS: st.session_state[f"ind_{field}"]=standardise_answer(bundle,field,person[field])
        for key,answer in zip(QUIZ,person["quiz"]): st.session_state[key]=answer
        st.session_state["answers"]={**{f:st.session_state[f"ind_{f}"] for f in FORM_FIELDS},"age":person["age"],"household_size":person["household_size"],"monthly_income":person["monthly_income"],"literacy_score":sum(a==QUIZ[k][2] for k,a in zip(QUIZ,person["quiz"]))}
        st.session_state["example_name"]=name
    except Exception:
        logger.exception("Illustrative profile failed to load | example=%s",name); st.error("We couldn't load that example profile. Please enter your answers manually.")

def show_suggestions(result, compact=False):
    for rank,(_,s) in enumerate(result["suggestions"].iterrows(),1):
        st.markdown(f'<div class="recommend-card"><span class="recommend-rank">{rank}</span><strong>{html.escape(str(s["display_name"]))}</strong><p>{html.escape(str(s["plain_sentence"]))}</p></div>',unsafe_allow_html=True)
        if not compact:
            with st.expander(f"Product details · {s['display_name']}"):
                st.markdown(f"- **Risk:** {s['risk']}\n- **Typical minimum:** {s['typical_minimum']}\n- **Getting your money out:** {s['access']}\n- **Time horizon:** {s['time_horizon']}\n- **Regulator:** {s['regulator']}")

apply_styles()
hero("Individual journey", "Explore options used by people like you", "Complete three short steps. Similarity matching uses the FinAccess survey, but you will not receive an investor-likelihood score or band.")

st.markdown("**Or try an illustrative profile:**")
cols=st.columns(len(EXAMPLE_PEOPLE))
for col,name in zip(cols,EXAMPLE_PEOPLE): col.button(name,on_click=load_example,args=(name,),use_container_width=True)
st.caption("Example profiles are illustrative and do not identify FinAccess survey respondents.")

step=st.session_state["ind_step"]
st.progress(step/3, text=f"Step {step} of 3")

if step==1:
    st.markdown('<span class="step-chip">Step 1 · About you</span>',unsafe_allow_html=True)
    st.markdown('<p class="section-intro">These details help identify survey respondents with broadly similar circumstances.</p>',unsafe_allow_html=True)
    with st.form("step_1"):
        c1,c2=st.columns(2)
        with c1:
            st.number_input("Age",value=None,step=1,placeholder="e.g. 30",key="ind_age")
            age_error=st.empty()
            st.selectbox("County",choices["county"],index=None,placeholder="Choose your county",key="ind_county")
            st.selectbox("Urban or rural area?",choices["urban_rural"],index=None,placeholder="Choose one",key="ind_urban_rural")
        with c2:
            st.number_input("How many people live in your household?",value=None,step=1,placeholder="e.g. 4",key="ind_household_size")
            household_error=st.empty()
            st.selectbox("Marital status",choices["marital_status"],index=None,placeholder="Choose one",key="ind_marital_status")
        next1=st.form_submit_button("Continue to financial profile →",type="primary",use_container_width=True)
    if next1:
        age=st.session_state.ind_age; hh=st.session_state.ind_household_size; bad=False
        if age is None: age_error.error("Please enter your age."); bad=True
        elif not MIN_AGE<=age<=MAX_AGE: age_error.error("Please enter an age between 16 and 105."); bad=True
        if hh is None: household_error.error("Please enter your household size."); bad=True
        elif not MIN_HOUSEHOLD_SIZE<=hh<=MAX_HOUSEHOLD_SIZE: household_error.error("Please enter a household size between 1 and 20."); bad=True
        missing=[x for x in ["ind_county","ind_urban_rural","ind_marital_status"] if st.session_state.get(x) is None]
        if missing: st.warning("Please complete all selections in this step."); bad=True
        if not bad: reset_results(); st.session_state.ind_step=2; st.rerun()

elif step==2:
    st.markdown('<span class="step-chip">Step 2 · Financial profile</span>',unsafe_allow_html=True)
    st.markdown('<p class="section-intro">Income may be left undisclosed. These fields support similarity matching, not a readiness score.</p>',unsafe_allow_html=True)
    with st.form("step_2"):
        c1,c2=st.columns(2)
        with c1:
            st.selectbox("Highest level of education",choices["education"],index=None,placeholder="Choose one",key="ind_education")
            st.selectbox("Main source of income / type of work",choices["livelihood"],index=None,placeholder="Choose one",key="ind_livelihood")
            st.number_input("Monthly income (KSh)",min_value=MIN_MONTHLY_INCOME,max_value=MAX_MONTHLY_INCOME,step=1000,placeholder="e.g. 15000",key="ind_income")
            st.checkbox("I prefer not to say my income",key="ind_prefer_not")
        with c2:
            st.selectbox("Do you have a national ID or passport?",choices["has_id"],key="ind_has_id",format_func=lambda x:"Yes" if x.lower().startswith("has id") else "No")
            st.selectbox("Do you use mobile money?",choices["mobile_money"],key="ind_mobile_money")
        b,n=st.columns(2)
        back2=b.form_submit_button("← Back",use_container_width=True)
        next2=n.form_submit_button("Continue to money questions →",type="primary",use_container_width=True)
    if back2: st.session_state.ind_step=1; st.rerun()
    if next2:
        missing=[x for x in ["ind_education","ind_livelihood"] if st.session_state.get(x) is None]
        if st.session_state.ind_income is None and not st.session_state.ind_prefer_not: missing.append("ind_income")
        if missing: st.warning("Please complete the education, work and income fields, or choose not to disclose income.")
        else: reset_results(); st.session_state.ind_step=3; st.rerun()

else:
    st.markdown('<span class="step-chip">Step 3 · Money questions</span>',unsafe_allow_html=True)
    st.markdown('<p class="section-intro">These are standard financial-literacy topics from the survey. They are not a pass-or-fail test.</p>',unsafe_allow_html=True)
    with st.form("step_3"):
        for key,(q,opts,_) in QUIZ.items(): st.radio(q,opts,index=None,key=key)
        b,s=st.columns(2)
        back3=b.form_submit_button("← Back",use_container_width=True)
        submit=s.form_submit_button("🔎 Find options used by people like me",type="primary",use_container_width=True)
    if back3: st.session_state.ind_step=2; st.rerun()
    if submit:
        unanswered=[k for k in QUIZ if st.session_state.get(k) is None]
        if unanswered: st.warning("Please answer all three money questions. 'I don't know' is a valid answer.")
        else:
            st.session_state.pop("example_name",None)
            st.session_state["answers"]={"age":st.session_state.ind_age,"urban_rural":st.session_state.ind_urban_rural,"county":st.session_state.ind_county,"education":st.session_state.ind_education,"marital_status":st.session_state.ind_marital_status,"household_size":st.session_state.ind_household_size,"livelihood":st.session_state.ind_livelihood,"monthly_income":None if st.session_state.ind_prefer_not else st.session_state.ind_income,"has_id":st.session_state.ind_has_id,"mobile_money":st.session_state.ind_mobile_money,"literacy_score":sum(st.session_state.get(k)==correct for k,(_,_,correct) in QUIZ.items())}
            st.rerun()

if "answers" in st.session_state:
    answers=st.session_state["answers"]
    try:
        with st.spinner("Finding people like you..."): result=recommend(bundle,answers)
    except Exception:
        logger.exception("Recommendation generation failed"); st.error("Sorry, we couldn't generate recommendations. Please check your answers and try again."); st.stop()
    st.divider(); st.subheader("Your suggested options")
    st.caption("Ranked from reported use among similar FinAccess respondents. These are educational suggestions, not suitability advice.")
    if result["starter_step"]: st.info("Few closely matched respondents use investment products, so starter options are prioritised.")
    show_suggestions(result)
    st.caption(f"You answered {answers['literacy_score']} of 3 money questions correctly.")
    with st.expander("Explore a what-if scenario",expanded=False):
        st.caption("What-if results show model sensitivity, not cause and effect.")
        c1,c2,c3=st.columns(3); what_if=dict(answers)
        what_if["education"]=c1.selectbox("Education",choices["education"],index=choices["education"].index(answers["education"]),key="wi_education")
        current=answers["monthly_income"] if answers["monthly_income"] is not None else 15000
        what_if["monthly_income"]=c2.number_input("Monthly income (KSh)",0,MAX_MONTHLY_INCOME,int(current),5000,key="wi_income")
        what_if["literacy_score"]=c3.slider("Money questions correct",0,3,int(answers["literacy_score"]),key="wi_literacy")
        if what_if==answers: st.caption("Change one input to compare.")
        else:
            try: wi_result=recommend(bundle,what_if)
            except Exception: logger.exception("Individual what-if failed"); st.error("We couldn't complete this comparison.")
            else:
                now,changed=st.columns(2)
                with now: st.markdown("**Current suggestions**"); show_suggestions(result,True)
                with changed: st.markdown("**Changed profile**"); show_suggestions(wi_result,True)

st.caption(DATA_NOTE); st.caption(DISCLAIMER); feedback_box("individuals")
