import pandas as pd
import json
import os
from langchain.tools import tool 

FINAL_INSIGHTS_PATH = "insights/final_product_insights.csv"
RELOCATION_PLAN_PATH = "insights/relocation_plan.csv"
MEMORY_FILE_PATH = "agent_memory/decision_log.json"

# Loading the Data
def _load_final_insights_df():
    if os.path.exists(FINAL_INSIGHTS_PATH):
        return pd.read_csv(FINAL_INSIGHTS_PATH)
    return pd.DataFrame()

def _load_relocation_plan_df():
    if os.path.exists(RELOCATION_PLAN_PATH):
        return pd.read_csv(RELOCATION_PLAN_PATH)
    return pd.DataFrame()

def _load_decision_log():
    if os.path.exists(MEMORY_FILE_PATH) and os.path.getsize(MEMORY_FILE_PATH) > 0:
        with open(MEMORY_FILE_PATH, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {MEMORY_FILE_PATH} is corrupted or empty. Starting with empty memory.")
                return []
    return []


@tool
def get_zone_performance(zone_id: str) -> str:
    """
    Provides detailed performance metrics for a specific store zone (e.g., 'A1', 'B5').
    Includes products in zone, total visits, online views of products, and zone category (Hot/Cold).
    """
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."
    
    zone_data = df[df['Zone'].str.upper() == zone_id.upper()]
    
    if zone_data.empty:
        return f"No data found for zone '{zone_id}'. Please provide a valid zone ID (e.g., 'A1')."
    
    zone_category = zone_data['Zone_Category'].iloc[0]
    total_zone_visits = zone_data['Visits'].sum() 
    
    products_in_zone = zone_data[['Product_Name', 'Visits', 'Online_Views']].to_dict(orient='records')
    
    response = f"Zone {zone_id.upper()} is categorized as **{zone_category}** with a total of **{total_zone_visits} in-store visits**."
    response += "\nProducts in this zone:\n"
    for prod in products_in_zone:
        response += f"- {prod['Product_Name']} (In-store visits: {prod['Visits']}, Online views: {prod['Online_Views']})\n"
    
    return response.strip()

@tool
def get_product_insights(product_name: str) -> str:
    """
    Provides detailed in-store and online performance for a specific product.
    Input should be the full product name (e.g., 'Bananas Dozen', 'Formal Shirt Men').
    """
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."
    
    product_data = df[df['Product_Name'].str.contains(product_name, case=False, na=False)]
    
    if product_data.empty:
        return f"No product found matching '{product_name}'. Please try a more precise name."
    
    # If multiple matches, take the first or ask for clarification
    product_data = product_data.iloc[0] 
    
    response = (
        f"Insights for **{product_data['Product_Name']}**:\n"
        f"- Current Zone: {product_data['Zone']} (Category: {product_data['Zone_Category']})\n"
        f"- In-store Visits: {product_data['Visits']}\n"
        f"- Online Views: {product_data['Online_Views']}\n"
    )
    
    return response.strip()

@tool
def get_relocation_recommendations(limit: int = 5) -> str:
    """
    Provides a summary of the top product relocation recommendations.
    Optionally, specify a 'limit' for the number of recommendations.
    """
    df = _load_relocation_plan_df()
    if df.empty:
        return "Relocation plan not available. Please ensure relocation_engine.py has been run."
    
    if limit <= 0:
        return "Limit must be a positive integer."

    recommendations = []
    for index, row in df.head(limit).iterrows():
        rec = (
            f"MOVE: **{row['Product_To_Move_In']}** (Online Views: {row['Cold_Product_Online_Views']}) "
            f"from Cold Zone {row['Current_Cold_Zone']} (Visits: {row['Cold_Zone_Visits']}) "
            f"TO Hot Zone {row['Suggested_New_Zone_For_Move_In']} "
            f"by replacing **{row['Product_To_Move_Out']}** (Hot Zone Visits: {row['Hot_Zone_Visits']})."
        )
        recommendations.append(rec)
    
    if not recommendations:
        return "No relocation recommendations available at this time."
    
    return "Top Relocation Recommendations:\n" + "\n".join(recommendations)

@tool
def get_past_relocation_outcome(product_name: str) -> str:
    """
    Checks the agent's memory for the outcome of a past relocation for a specific product.
    Input should be the full product name that was moved (e.g., 'Dettol').
    """
    memory_log = _load_decision_log()
    if not memory_log:
        return "Agent memory is empty. No past relocation outcomes to report."
    
    relevant_moves = [
        m for m in memory_log 
        if m.get("action_type") == "relocation" and 
        product_name.lower() in m.get("product_moved_in_name", "").lower()
    ]
    
    if not relevant_moves:
        return f"No past relocation record found for '{product_name}' in agent's memory."
    
    # Sort by latest move if multiple
    relevant_moves.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    latest_move = relevant_moves[0]
    
    response = (
        f"According to my memory, **{latest_move['product_moved_in_name']}** "
        f"was moved from {latest_move['from_zone']} to {latest_move['to_zone']} "
        f"on {latest_move['timestamp']} (replacing {latest_move.get('product_replaced_name', 'an old product')}).\n"
        f"The **simulated outcome was: {latest_move['simulated_outcome']}**."
    )
    return response.strip()

@tool
def list_hot_cold_zones() -> str:
    """
    Lists the number of 'Hot' and 'Cold' zones in the store and provides examples.
    """
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."
    
    zone_categories = df.groupby('Zone_Category')['Zone'].apply(lambda x: list(x.unique())).to_dict()
    
    hot_zones_count = len(zone_categories.get('Hot', []))
    cold_zones_count = len(zone_categories.get('Cold', []))
    
    hot_examples = ", ".join(zone_categories.get('Hot', [])[:3])
    cold_examples = ", ".join(zone_categories.get('Cold', [])[:3])
    
    response = (
        f"The store currently has **{hot_zones_count} Hot zones** (e.g., {hot_examples}) "
        f"and **{cold_zones_count} Cold zones** (e.g., {cold_examples}).\n"
        f"Hot zones are areas with high customer visits, while cold zones have lower traffic."
    )
    return response.strip()