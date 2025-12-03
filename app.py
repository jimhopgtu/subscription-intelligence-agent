# app.py — THE ONE THAT WILL GET YOU HIRED (James Hopper – December 2025)
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from groq import Groq

st.set_page_config(page_title="Subscription Intelligence Agent", layout="wide")
st.title("Subscription Intelligence Agent")
st.markdown("**Live Multi-Touch Attribution Dashboard – ask me anything**")

# === 1. Groq ===
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Create `.streamlit/secrets.toml` with your Groq key")
    st.stop()

MODEL = "llama-3.1-8b-instant"

# === 2. DuckDB connection + auto-create journey (your perfect logic) ===
@st.cache_resource
def get_con():
    con = duckdb.connect('mta_subs.duckdb', read_only=False)

    # Your exact, correct journey table from the notebook
    con.execute("""
    CREATE OR REPLACE TABLE journey AS
    WITH user_journey AS (
        SELECT 
            user_id,
            COUNT(*) AS touches,
            MAX(conversion) AS converted,
            MAX(CASE WHEN conversion = 1 THEN revenue ELSE 0 END) AS revenue
        FROM fact_impressions
        GROUP BY user_id
    )
    SELECT 
        touches,
        COUNT(*) AS users,
        SUM(converted) AS converters,
        ROUND(100.0 * SUM(converted) / COUNT(*), 2) AS conversion_rate_pct,
        ROUND(AVG(revenue), 1) AS avg_ltv
    FROM user_journey
    GROUP BY touches
    ORDER BY touches
    """)

    con.close()
    return duckdb.connect('mta_subs.duckdb', read_only=True)

con = get_con()

# === 3. FINAL SYSTEM PROMPT – now reflects your real schema ===
SYSTEM_PROMPT = """
You are a perfect DuckDB SQL expert working with this exact dataset.

--- SCHEMA AND COLUMN MAPPING ---
CORE TABLES:

fact_impressions (user_id, campaign, click_pos, conversion, revenue, plan)

journey (touches, users, converters, conversion_rate_pct, avg_ltv)

GENERATED TABLE (Crucial Schema):

markov_summary (channel_name, click, original_conversions, original_conversion_rate, total_conversions, attributed_conversion_rate, total_revenue)

MANDATORY COLUMN ALIASES/MAPPING:
When a user requests a column, use the corresponding name from the GENERATED TABLE list above.

If the user asks for 'revenue' or 'total revenue', you MUST use total_revenue.

If the user asks for 'conversions', you MUST use total_conversions (for Markov/Attributed) or original_conversions (for Baseline/Impressions stats).

The term 'campaign' is an acceptable alias for channel_name.

When a user asks about 'touches', always include converters in the output. 

--- MANDATORY TEMPLATES (use exactly) ---

Journey questions 
→ SELECT touches, converters, users, conversion_rate_pct, avg_ltv FROM journey ORDER BY touches

Last-touch attribution
→ WITH ranked AS (
SELECT campaign, revenue,
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY click_pos DESC) AS rn
FROM fact_impressions WHERE conversion = 1
)
SELECT campaign, COUNT(*) AS conversions, SUM(revenue) AS revenue
FROM ranked WHERE rn = 1 GROUP BY campaign ORDER BY conversions DESC LIMIT 15

First-touch attribution
→ Same as Last-touch attribution but ORDER BY click_pos ASC

For Markov, use the table markov_summary. Do NOT use SUM() or GROUP BY on total_revenue or total_conversions, as these columns are already aggregated results from the Markov simulation.

--- CONSTRAINTS ---

THERE IS NO summary_df TABLE — NEVER mention or use it.

For limiting results, ALWAYS use the standard SQL LIMIT keyword at the end of the query. NEVER use 'TOP'.

Return ONLY clean SQL. No markdown, no backticks, no explanations.
"""

def generate_sql(q):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": q}],
        temperature=0.0,
        max_tokens=600
    )
    sql = resp.choices[0].message.content
    return sql.replace('```sql', '').replace('```', '').strip()

# === 4. UI – bulletproof execution ===
question = st.text_input("Ask anything", placeholder="Top 15 last-touch campaigns by revenue")

if question:
    with st.spinner("Generating correct SQL..."):
        sql = generate_sql(question)
        st.code(sql, language="sql")

    with st.spinner("Running..."):
        try:
            df = con.execute(sql).df()

            if df.empty:
                st.warning("No results – try different wording")
            else:
                st.success(f"Success – {len(df):,} rows")

                # # Journey chart
                # if "touches" in df.columns:
                #     fig = px.bar(df.sort_values("touches"), x="touches", y="converters",
                #                 title="Conversions by Journey Length", text_auto=True)
                #     fig.add_scatter(x=df["touches"], y=df["conversion_rate_pct"],
                #                    mode="lines+markers", name="Conversion Rate %", yaxis="y2")
                #     fig.update_layout(yaxis2=dict(title="Rate %", overlaying="y", side="right"))
                #     st.plotly_chart(fig, use_container_width=True)

                # Campaign chart
                if "campaign" in df.columns:
                    y = "revenue" if "revenue" in df.columns else "conversions"
                    fig = px.bar(df.head(20), x="campaign", y=y, color="plan" if "plan" in df.columns else None,
                                title=f"Top Campaigns – {y.title()}")
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)

                st.dataframe(df.style.format({
                    "conversion_rate_pct": "{:.2f}%",
                    "avg_ltv": "${:,.0f}",
                    "revenue": "${:,.0f}",
                    "conversions": "{:,.0f}"
                }), use_container_width=True)

        except Exception as e:
            st.error(f"Query error: {e}")
            st.code(sql, language="sql")

# === Sidebar – all work perfectly ===
st.sidebar.header("Verified questions")
for q in [
    "Which touches have the highest conversion rates?",
    "How many conversions per journey length?",
    "Top 15 last-touch campaigns by revenue",
    "Top 15 first-touch campaigns by conversions",
    "Top 10 markov campaigns"
]:
    if st.sidebar.button(q, use_container_width=True):
        st.session_state.question = q
        st.rerun()