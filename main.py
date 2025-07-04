import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
import json

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from heatsight_tools import (
    get_zone_performance,
    get_product_insights,
    get_relocation_recommendations,
    get_past_relocation_outcome,
    list_hot_cold_zones
)

load_dotenv()

st.set_page_config(
    layout="wide",
    page_title="HeatSight: Walmart Omnichannel Insights",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #000000;
        color: #f0f0f0;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #007ACC;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    h1 {
        font-size: 2.5em;
        text-align: center;
        padding-bottom: 20px;
        border-bottom: 2px solid #007ACC;
        margin-bottom: 30px;
        color: #007ACC;
    }

    .stMarkdown {
        font-family: 'Arial', sans-serif;
        font-size: 1.1em;
        line-height: 1.6;
        color: #f0f0f0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        background-color: #1a1a1a;
        border-radius: 8px 8px 0 0;
        gap: 10px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 20px;
        padding-right: 20px;
        font-size: 1.1em;
        color: #b0b0b0;
        font-weight: bold;
    }

    .stTabs [data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
        font-size: 1.1em;
        font-weight: bold;
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: #2a2a2a;
        color: #007ACC;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #007ACC;
        color: white;
        border-bottom: 3px solid #FFC300;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        background-color: #121212;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
        margin-bottom: 30px;
    }

    .stSidebar {
        background-image: linear-gradient(to bottom, #007ACC, #014E7B);
        color: white;
        padding-top: 30px;
    }
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, h6,
    .stSidebar .stMarkdown, .stSidebar .stInfo {
        color: white !important;
        font-weight: bold;
    }
    .stSidebar .stButton>button {
        width: 90%;
        margin-left: 5%;
        margin-right: 5%;
        border-radius: 10px;
        background-color: #FFC300;
        color: #014E7B;
        font-weight: bold;
    }

    .stChatMessage {
        border-radius: 10px;
        padding: 10px 15px;
        margin-bottom: 10px;
    }
    .stChatMessage.st-ai-message {
        background-color: #222222;
        border-left: 5px solid #007ACC;
        color: #f0f0f0;
    }
    .stChatMessage.st-human-message {
        background-color: #1a1a1a;
        border-right: 5px solid #007ACC;
        text-align: right;
        margin-left: auto;
        color: #f0f0f0;
    }
    .stChatMessage.st-human-message > div > div > div > div {
        text-align: right;
    }

    [data-testid="stMetric"] {
        background-color: #121212;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        color: #f0f0f0;
    }
    [data-testid="stMetric"] label {
        color: #b0b0b0;
    }
    [data-testid="stMetric"] .stMetricValue {
        color: #FFC300;
    }
    [data-testid="stMetric"] .stMetricDelta {
        color: #4CAF50;
    }
    [data-testid="stMetric"] .stMetricDelta[data-testid="stMetricDelta"] {
        color: #F44336;
    }

    .stPlotlyChart {
        background-color: #121212;
        border-radius: 10px;
        overflow: hidden;
    }
    .stPlotlyChart .modebar-container {
        background-color: #121212 !important;
    }

</style>
""", unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

def display_message(message):
    message_type_class = "st-ai-message" if message.type == "ai" else "st-human-message"
    with st.chat_message(message.type, avatar="🤖" if message.type == "ai" else "🧑‍💻"):
        st.markdown(message.content, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Walmart_logo_2017.svg/1200px-Walmart_logo_2017.svg.png", width=200)
    st.title("💡 HeatSight Dashboard")
    st.markdown("""
    **Your Omnichannel Retail Intelligence Platform.**
    HeatSight leverages in-store customer movement and online product performance to provide
    actionable insights for optimized store layouts and enhanced customer experience.
    """)
    st.markdown("---")
    st.subheader("🚀 Project Status:")
    st.info("AI Agent 'ShelfSense' is now integrated!")
    st.markdown("---")
    if st.button("Refresh Data"):
        st.experimental_rerun()

st.title("🛒 HeatSight: Revolutionizing Walmart Retail with Omnichannel Insights")
st.markdown("""
<p style='text-align: center; font-size: 1.2em; color: #f0f0f0;'>
Welcome to HeatSight, an innovative solution for Walmart's Sparkathon! This platform intelligently optimizes store layouts, reduces stockouts, and enhances customer experience by bridging the gap between physical and digital customer engagement.
</p>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard Overview",
    "🔥 In-Store Heatmap",
    "📈 Omnichannel Insights",
    "📦 Relocation Plan",
    "🤖 ShelfSense AI Agent"
])

with tab1:
    st.header("📊 Dashboard Overview: Key Metrics")
    st.markdown("A quick glance at the core operational metrics derived from our simulated data.")

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    total_zones = 100
    col_kpi1.metric("Total Store Zones", total_zones)

    try:
        final_insights_df = pd.read_csv("insights/final_product_insights.csv")
        hot_zones_count = final_insights_df[final_insights_df["Zone_Category"] == "Hot"]["Zone"].nunique()
        cold_zones_count = final_insights_df[final_insights_df["Zone_Category"] == "Cold"]["Zone"].nunique()
        col_kpi2.metric("Hot Zones 🔥", hot_zones_count, delta=f"{hot_zones_count/total_zones:.1%}")
        col_kpi3.metric("Cold Zones ❄️", cold_zones_count, delta=f"-{cold_zones_count/total_zones:.1%}")
    except FileNotFoundError:
        st.warning("Run `final_insights.py` to see Hot/Cold Zone metrics.")
        col_kpi2.metric("Hot Zones 🔥", "N/A")
        col_kpi3.metric("Cold Zones ❄️", "N/A")

    st.markdown("---")
    st.subheader("Project Mission")
    st.markdown("""
    Our mission with HeatSight is to empower Walmart store managers with **actionable intelligence**
    to transform their physical retail spaces. By understanding how customers move in-store and how
    products perform online, we aim to:

    * **Optimize Product Placement:** Ensure high-demand items are in high-traffic areas.
    * **Reduce Stockouts:** Proactively manage inventory based on predicted demand.
    * **Enhance Customer Journey:** Create a more intuitive and satisfying shopping experience.
    * **Drive Sales Growth:** Leverage data to maximize revenue per square foot.
    """)
    st.image("https://media.istockphoto.com/id/1149725807/photo/young-african-woman-using-her-smartphone-in-grocery-store.jpg?s=612x612&w=0&k=20&c=p-bT69k32h6y6-iS9zYk8D5eM5_B-Q1oTf4S6Z5g2-U=", caption="Connecting Online & Offline Customer Journeys", use_column_width=True)


with tab2:
    st.header("🔥 In-Store Customer Movement Heatmap")
    st.markdown("""
    Visualizing customer traffic patterns across the store's 10x10 grid.
    <span style='color: #FFC300; font-weight: bold;'>Darker reds indicate 'Hot' zones with higher customer visits</span>,
    while lighter areas are 'Cold' zones.
    """, unsafe_allow_html=True)

    try:
        movement_df = pd.read_csv("data/movements.csv")
        zone_counts = movement_df["Zone"].value_counts().to_dict()

        rows = [chr(ord('A') + i) for i in range(10)]
        cols = range(1, 11)

        heatmap_grid = np.zeros((len(rows), len(cols)), dtype=int)
        for r_idx, row_label in enumerate(rows):
            for c_idx, col_label in enumerate(cols):
                zone_name = f"{row_label}{col_label}"
                heatmap_grid[r_idx, c_idx] = zone_counts.get(zone_name, 0)

        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(heatmap_grid, annot=True, fmt="d", cmap="YlOrRd",
                    xticklabels=cols, yticklabels=rows, linewidths=.5, linecolor='lightgray', ax=ax)
        ax.set_title("Heatmap of In-Store Zone Visits", fontsize=16, color='#f0f0f0')
        ax.set_xlabel("Shelf Column", fontsize=12, color='#f0f0f0')
        ax.set_ylabel("Shelf Row", fontsize=12, color='#f0f0f0')
        ax.tick_params(axis='x', rotation=0, colors='#e0e0e0')
        ax.tick_params(axis='y', rotation=0, colors='#e0e0e0')
        ax.set_facecolor('#121212')
        fig.patch.set_facecolor('#121212')
        plt.tight_layout()
        st.pyplot(fig)

    except FileNotFoundError:
        st.error("Error: 'data/movements.csv' not found. Please run `movements.py`.")
    except Exception as e:
        st.error(f"Error generating heatmap: {e}")


with tab3:
    st.header("📈 Omnichannel Insights: Bridging Digital & Physical")
    st.markdown("""
    This section merges in-store customer movement data with online product performance to reveal comprehensive insights.
    Understand which products are popular online versus their in-store visibility.
    """)

    try:
        final_insights_df = pd.read_csv("insights/final_product_insights.csv")
        st.dataframe(final_insights_df)

        st.subheader("Zone Category Distribution")
        col_dist1, col_dist2 = st.columns(2)
        with col_dist1:
            st.write("Breakdown of Hot vs. Cold Zones by Count:")
            zone_category_counts = final_insights_df["Zone_Category"].value_counts()
            fig_cat, ax_cat = plt.subplots(figsize=(6, 4))
            zone_category_counts.plot(kind='bar', ax=ax_cat, color=['#FFC300', '#007ACC'])
            ax_cat.set_title("Distribution of Hot vs. Cold Zones", color='#f0f0f0')
            ax_cat.set_ylabel("Number of Zones", color='#f0f0f0')
            ax_cat.set_xlabel("Zone Category", color='#f0f0f0')
            ax_cat.tick_params(axis='x', rotation=0, colors='#e0e0e0')
            ax_cat.tick_params(axis='y', colors='#e0e0e0')
            ax_cat.set_facecolor('#121212')
            fig_cat.patch.set_facecolor('#121212')
            st.pyplot(fig_cat)
        
        with col_dist2:
            st.write("Top 10 Products by Online Views:")
            top_online = final_insights_df.sort_values(by="Online_Views", ascending=False).head(10)
            st.dataframe(top_online[['Product_Name', 'Online_Views', 'Zone', 'Zone_Category']])
            st.markdown("These products have high digital interest. Are they easy to find in-store?")

    except FileNotFoundError:
        st.error("Error: 'insights/final_product_insights.csv' not found. Please run `final_insights.py`.")


with tab4:
    st.header("📦 Smart Relocation Plan: Actionable Optimization")
    st.markdown("""
    This section presents actionable insights: products in cold zones with high online demand are suggested to be moved
    to hot zones currently occupied by underperforming products. This strategy aims to maximize visibility and sales.
    """)

    try:
        relocation_df = pd.read_csv("insights/relocation_plan.csv")
        
        if not relocation_df.empty:
            st.dataframe(relocation_df)
            
            st.subheader("Summary of Relocation Plan")
            st.info(f"✨ **ShelfSense recommends {len(relocation_df)} strategic product swaps today!**")
            st.write("This plan aims to maximize visibility for high-demand online products by placing them in high-traffic store areas, while optimizing space from underperforming items.")
        else:
            st.info("No new relocation suggestions generated for this cycle. The store layout might already be highly optimized or new opportunities haven't emerged.")

    except FileNotFoundError:
        st.error("Error: 'insights/relocation_plan.csv' not found. Please run `relocation_engine.py`.")


with tab5:
    st.header("🤖 ShelfSense AI Agent: Your Smart Retail Co-Pilot")
    st.markdown("""
    Ask ShelfSense anything about store performance, product insights, or relocation plans.
    It can analyze data, explain trends, and provide recommendations using its intelligent tools and memory.
    """)

    tools = [
        get_zone_performance,
        get_product_insights,
        get_relocation_recommendations,
        get_past_relocation_outcome,
        list_hot_cold_zones
    ]

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
        
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are ShelfSense, a highly intelligent and helpful AI assistant for Walmart store managers. "
                    "Your primary goal is to provide data-driven insights and actionable recommendations for optimizing store layouts and product placements based on in-store traffic and online performance. "
                    "You have access to tools to retrieve information about store zones, products, and relocation plans, and to recall past decisions. "
                    "Always be concise, precise, and polite. If you need more information to answer a question accurately, ask follow-up questions (e.g., 'Could you please specify the product name?' or 'Which zone are you asking about?'). "
                    "When answering about relocation plans, clearly mention the product to move in, its online views, its current cold zone, and the suggested hot zone it should move to (by replacing another product). "
                    "When asked about past outcomes, use your memory tool (`get_past_relocation_outcome`) to find specific results and state the simulated outcome clearly. "
                    "If you cannot find relevant information with your tools, state that clearly and suggest what information you can provide instead. "
                    "Use emojis appropriately to make your responses more engaging where suitable (e.g., 🔥 for hot, ❄️ for cold, 📦 for relocation)."
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        conversational_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, memory=conversational_memory)

        st.info("ShelfSense is ready to assist! Try asking: 'What are the top relocation recommendations?' or 'Tell me about product Formal Shirt Men.'")

        for msg in st.session_state.messages:
            display_message(msg)

        if user_query := st.chat_input("Ask ShelfSense..."):
            st.session_state.messages.append(HumanMessage(content=user_query, type="human"))
            display_message(HumanMessage(content=user_query, type="human"))

            with st.spinner("ShelfSense is thinking..."):
                try:
                    response = agent_executor.invoke({"input": user_query})
                    ai_response_content = response["output"]

                    st.session_state.messages.append(AIMessage(content=ai_response_content, type="ai"))
                    display_message(AIMessage(content=ai_response_content, type="ai"))

                except Exception as e:
                    st.error(f"Error interacting with ShelfSense: {e}")
                    st.warning("Please ensure your `GOOGLE_API_KEY` is correctly set, you have internet access, and API limits are not hit.")
                    st.session_state.messages.append(AIMessage(content="I apologize, but I encountered an error while processing your request. Please try again or rephrase your question. Ensure all data generation scripts (`store_layout.py` etc.) have been run.", type="ai"))
                    display_message(AIMessage(content="I apologize, but I encountered an error while processing your request. Please try again or rephrase your question. Ensure all data generation scripts (`store_layout.py` etc.) have been run.", type="ai"))

    except Exception as e:
        st.error(f"Could not initialize Google Gemini LLM or ShelfSense Agent. Error: {e}")
        st.warning("Please check your `GOOGLE_API_KEY` in the `.env` file, ensure `langchain-google-genai` is installed, or review previous error messages in your console.")

st.markdown("---")