"""Money words explained: the products in the app and common money words, in plain language."""
import streamlit as st

from common import footer, get_bundle
from styles import glossary_card, hero

bundle = get_bundle()
products = bundle["recommender"]["product_reference"]

MONEY_WORDS = {
    "Interest": "Money paid to you for saving, or that you pay for borrowing. Usually shown as a % per year.",
    "Inflation": "Prices going up over time. If your savings earn less than inflation, they buy less each year.",
    "Return": "What you earn on money you put somewhere: interest, dividends or a rise in value.",
    "Risk": "The chance that you get back less than you expected, or less than you put in.",
    "Spreading risk (diversification)": "Putting money in several places, so one loss doesn't hurt everything.",
    "Getting your money out (liquidity)": "How quickly you can turn an investment back into cash without losing value.",
    "Time horizon": "How long you plan to leave the money before you need it.",
    "Dividend": "A share of a company's profits paid to the people who own its shares.",
    "Shares (stocks)": "Owning a small part of a company listed on the Nairobi Securities Exchange. "
                       "The price goes up and down.",
    "Money market fund": "A fund that pools many people's money and puts it in short-term, lower-risk "
                         "investments. Run by a licensed fund manager.",
    "Unit trust": "A pool of many people's money managed by a licensed fund manager. A money market fund is "
                  "one type of unit trust.",
    "Treasury bills and bonds": "Loans to the Kenyan government. Bills last up to one year; bonds last longer. "
                                "Sold through the Central Bank of Kenya.",
    "SACCO": "A savings and credit co-operative owned by its members. Members save and can borrow.",
    "Chama": "A group that saves or invests together under its own agreed rules.",
    "Pension": "Long-term saving for retirement. The money is usually locked until you retire.",
}
REGULATORS = {
    "CBK (Central Bank of Kenya)": "Banks and microfinance banks. Also runs the sale of Treasury bills and bonds.",
    "CMA (Capital Markets Authority)": "Shares, unit trusts, money market funds and fund managers.",
    "SASRA": "SACCOs that take deposits.",
    "RBA (Retirement Benefits Authority)": "Pension schemes.",
    "IRA (Insurance Regulatory Authority)": "Insurance companies and insurance products.",
}

hero("Money words explained", "Saving and investing, in plain words",
     "What each option in this app means, and the money words you will see on the way.")

search = st.text_input("Search for a word", placeholder="e.g. money market fund, SACCO, inflation").strip().lower()


def matches(*texts):
    return not search or any(search in str(t).lower() for t in texts)


st.subheader("The options in this app")
shown = 0
columns = st.columns(2, gap="medium")
for _, product in products.iterrows():
    details = [("Risk", product.get("risk")), ("Typical minimum", product.get("typical_minimum")),
               ("Getting your money out", product.get("access")), ("Time horizon", product.get("time_horizon")),
               ("Regulator", product.get("regulator"))]
    if matches(product.get("display_name"), *[text for _, text in details]):
        with columns[shown % 2]:
            glossary_card(product.get("display_name"),
                          [(label, text) for label, text in details if isinstance(text, str) and text.strip()])
        shown += 1
if not shown:
    st.caption("No options match your search.")

st.subheader("Money words")
words = [(word, meaning) for word, meaning in MONEY_WORDS.items() if matches(word, meaning)]
columns = st.columns(2, gap="medium")
for i, (word, meaning) in enumerate(words):
    with columns[i % 2]:
        glossary_card(word, [("", meaning)])
if not words:
    st.caption("No money words match your search.")

st.subheader("Who checks the providers")
st.write("Before you put money anywhere, check that the provider is licensed by the right regulator, "
         "on that regulator's website.")
for name, covers in REGULATORS.items():
    if matches(name, covers):
        st.markdown(f"- **{name}:** {covers}")

st.page_link("views/ask_ai.py", label="Still unsure? Ask the AI a question", icon=":material/chat:")
footer("glossary")
