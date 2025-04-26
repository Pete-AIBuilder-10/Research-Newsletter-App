import os
import streamlit as st
import openai
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

# -------------- CONFIG -------------------
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure your API key is set in environment

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.finextra.com/rss/finextranews.aspx",
    "https://cointelegraph.com/rss",
    "https://thefinancialbrand.com/feed/",
    "https://news.google.com/rss/search?q=artificial+intelligence",
    "https://news.google.com/rss/search?q=payments",
    "https://news.google.com/rss/search?q=stablecoins",
    "https://news.google.com/rss/search?q=banking+innovation",
    "https://news.google.com/rss/search?q=fintech"
]

TOPICS = [
    "Artificial Intelligence", "Machine Learning", "Generative AI", "Agentic AI", "Explainable AI (XAI)", "Quantum Computing", "Robotics in Finance",
    "Payments Innovation", "Digital Wallets", "CBDCs (Central Bank Digital Currencies)", "Stablecoins", "Tokenization of Assets", "Cross-Border Payments", "Real-Time Payments",
    "Open Banking", "Digital Banking Transformation", "Embedded Finance", "Banking-as-a-Service (BaaS)", "Core Banking Modernization",
    "Fintech M&A", "WealthTech", "InsurTech", "LendingTech (BNPL)", "Challenger Banks (Neobanks)", "Super Apps",
    "Cryptocurrency Regulation", "DeFi (Decentralized Finance)", "Crypto Custody Solutions", "Smart Contracts Development", "ESG in Finance"
]

MAX_ARTICLES = 5  # Max number of articles processed per run
MIN_SUMMARY_LENGTH = 300  # Minimum length of clean summaries to accept

# ------------------------------------------

# -------------- APP START -----------------
st.set_page_config(page_title="Strategic Research Newsletter", page_icon="📰", layout="centered")

st.title("📰 Strategic Research Newsletter Builder")
st.write("Select your topics, click generate, and get a custom AI-powered newsletter.")

selected_topics = st.multiselect(
    "Choose your research topics:",
    TOPICS,
    default=["Artificial Intelligence", "Payments Innovation"]
)

generate_button = st.button("Generate Newsletter")

if generate_button and selected_topics:
    with st.spinner('Fetching articles and generating newsletter...'):

        # -------------- ARTICLE FETCHING --------------
        topic_keywords = [t.lower() for t in selected_topics]
        articles = []

        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                raw_summary = getattr(entry, 'summary', "No summary available.")
                summary = BeautifulSoup(raw_summary, "html.parser").get_text().strip()

                # New length filter
                if len(summary) < MIN_SUMMARY_LENGTH:
                    continue  # Skip articles with too-short summaries

                if any(keyword in title.lower() or keyword in summary.lower() for keyword in topic_keywords):
                    articles.append((title, link, summary))

        if not articles:
            st.error("No high-quality articles found for selected topics. Try expanding your selection!")
            st.stop()

        articles = articles[:MAX_ARTICLES]
        st.success(f"Found {len(articles)} strong articles.")

        # -------------- DYNAMIC TITLE -------------------
        combined_titles = "\n".join([title for title, link, summary in articles])

        try:
            title_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a newsletter editor. Create a short, strategic title (under 6 words) capturing this week's dominant theme."},
                    {"role": "user", "content": f"Here are the article titles:\n\n{combined_titles}\n\nSuggest a newsletter title."}
                ],
                temperature=0.5,
                max_tokens=50
            )
            dynamic_title = title_response.choices[0].message.content.strip()
        except Exception as e:
            dynamic_title = "Weekly Strategic Insights"

        # -------------- NEWSLETTER BUILD ----------------
        newsletter = f"# 🗞️ {dynamic_title}\n\n"

        newsletter += "## 📌 Caught My Eye\n"
        for title, link, summary in articles:
            newsletter += f"- [{title}]({link}): {summary}\n\n"

        newsletter += "\n## 🔍 The So What\n"

        for title, link, summary in articles:
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a strategy consultant. For this article, write:\n- Impact\n- Signal\n- Long-term Implication"},
                        {"role": "user", "content": f"Article Summary: {summary}\n\nWrite the strategic analysis."}
                    ],
                    temperature=0.5,
                    max_tokens=300
                )
                insights = response.choices[0].message.content
                newsletter += f"**{title}**\n{insights}\n\n"
            except Exception as e:
                newsletter += f"**{title}**\n- Strategic analysis unavailable.\n\n"

        # -------------- KEY TAKEAWAYS ----------------
        combined_summaries = "\n".join([f"Title: {title}\nSummary: {summary}" for title, link, summary in articles])

        try:
            takeaway_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a strategy consultant analyzing this week's newsletter. Identify 3–5 major emerging strategic themes from these articles."},
                    {"role": "user", "content": f"Here are this week's articles:\n\n{combined_summaries}\n\nSummarize the major strategic takeaways."}
                ],
                temperature=0.4,
                max_tokens=300
            )
            key_takeaways = takeaway_response.choices[0].message.content
        except Exception as e:
            key_takeaways = "- Themes extracted from real articles.\n- Market signals spotted.\n- Strategic responses anticipated."

        newsletter += "\n## 🧠 Key Takeaways\n"
        newsletter += key_takeaways + "\n"

        # -------------- SHOW NEWSLETTER ----------------
        st.subheader("📄 Generated Newsletter Preview")
        st.markdown(newsletter)

        # -------------- DOWNLOAD FILE ----------------
        today = datetime.today().strftime('%Y-%m-%d')
        filename = f"newsletter_{today}.md"

        st.download_button(
            label="📥 Download Newsletter (.md)",
            data=newsletter,
            file_name=filename,
            mime="text/markdown"
        )
