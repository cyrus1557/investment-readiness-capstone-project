"""Model and fairness: how well the models work, what drives results, and how fair they are (from the notebook)."""
import altair as alt
import pandas as pd
import streamlit as st

from common import footer
from styles import COLORS, hero, note

hero("Model and fairness", "How well it works, and for whom",
     "Results from our notebook, measured on people the model never saw during training.")

# Headline test results (notebook 6.1 and 6.2)
st.subheader("Test results")
m1, m2, m3, m4 = st.columns(4)
m1.metric("PR-AUC", "0.233", help="Main score for rare outcomes. Random guessing scores 0.027.")
m2.metric("Better than random", "8.6×")
m3.metric("Investors found (High band)", "53%", help="Recall at the 8% cut-off.")
m4.metric("High band who invest", "14.3%", help="Precision: 5.3 times the 2.7% average.")


def bar_chart(data, x, y, highlight, x_title, sort="-x", fmt=".3f", height=260):
    # Horizontal bars, one highlighted in gold, value labels at the end of each bar
    base = alt.Chart(data).encode(
        y=alt.Y(f"{y}:N", sort=sort, title=None, axis=alt.Axis(labelFontSize=13, labelLimit=260)),
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(labelFontSize=12)),
    )
    bars = base.mark_bar(cornerRadiusEnd=6, size=24).encode(
        color=alt.condition(alt.datum[y] == highlight, alt.value(COLORS["gold"]), alt.value(COLORS["green"])),
        tooltip=[y, alt.Tooltip(x, format=fmt)])
    labels = base.mark_text(align="left", dx=5, fontSize=13, color=COLORS["text"]).encode(
        text=alt.Text(f"{x}:Q", format=fmt))
    return (bars + labels).properties(height=height)


left, right = st.columns(2, gap="large")
with left:
    st.subheader("Models compared")
    models = pd.DataFrame({
        "Model": ["Random guessing", "Logistic regression", "Random forest", "XGBoost",
                  "Tuned random forest", "Tuned XGBoost (chosen)"],
        "PR-AUC": [0.027, 0.174, 0.180, 0.185, 0.196, 0.196],
    })
    st.altair_chart(bar_chart(models, "PR-AUC", "Model", "Tuned XGBoost (chosen)", "PR-AUC (5-fold average)",
                              sort=None), use_container_width=True)
    st.caption("The two tuned models tied on average. XGBoost won 4 of the 5 rounds and varied less, so we chose it.")
with right:
    st.subheader("What drives the likelihood")
    drivers = pd.DataFrame({
        "Answer": ["Education", "Monthly income", "County", "Age", "Type of work"],
        "Average push": [0.720, 0.679, 0.391, 0.336, 0.238],
    })
    st.altair_chart(bar_chart(drivers, "Average push", "Answer", "Education", "Average SHAP push (size)"),
                    use_container_width=True)
    st.caption("From SHAP: how much each answer moves a person's likelihood up or down, on average.")

st.subheader("The likelihood bands")
st.dataframe(pd.DataFrame({
    "Band": ["High", "Medium", "Low"],
    "Likelihood": ["8% or more", "3% to 8%", "Below 3%"],
    "Who actually invested (test data)": ["14.3%", "5.0%", "0.8%"],
}), hide_index=True, use_container_width=True)
st.caption("The High band is about 10% of people but holds 53% of all investors.")

note("info", "Calibrated: the percentages mean what they say.",
     "Before calibration the model's average prediction was 28.2%. After calibration it is 2.7%, the same as "
     "the real share of investors.")

st.subheader("Fairness")
f1, f2 = st.columns(2, gap="large")
with f1:
    st.markdown("**Investors found by the model (at the 8% cut-off)**")
    st.dataframe(pd.DataFrame({
        "Group": ["Women", "Men", "Age 16–34", "Age 55+"],
        "Investors found": ["53%", "53%", "41%", "70%"],
    }), hide_index=True, use_container_width=True)
    st.caption("Women and men are found equally well. Younger adults are harder to find.")
with f2:
    st.markdown("**Why sex is left out**")
    st.markdown(
        "- Adding sex would raise the score only a little (0.202 vs 0.196).\n"
        "- No one should get a lower likelihood because of their sex, so it is never used.\n"
        "- It is kept aside only to check fairness, like the table on the left.\n"
        "- Women still get starter suggestions more often (62% vs 41% of men), because the people most similar "
        "to them invest less today (2.0% of women vs 4.4% of men)."
    )

st.subheader("The recommender (for individuals)")
st.dataframe(pd.DataFrame({
    "Option": ["Pension", "Shares", "SACCO"],
    "Users it found": ["83.8%", "57.5%", "43.3%"],
    "Of those suggested, share who use it": ["37.2%", "7.8%", "14.2%"],
    "Average Kenyan adult": ["12.8%", "2.8%", "17.6%"],
}), hide_index=True, use_container_width=True)
st.caption("For pensions and shares, people we suggest them to use them far more than average. "
           "SACCO suggestions are weaker, which we list as a limit.")

footer("model")
