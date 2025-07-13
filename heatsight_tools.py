import pandas as pd
import json
import os
from datetime import datetime
from langchain.tools import tool

# --- Configuration ---
# Define core directories relative to the project root
DATA_DIR = "data"
INSIGHTS_DIR = "insights"
AGENT_MEMORY_DIR = "agent_memory"

# Define full paths for all data files
STORE_LAYOUT_PATH = os.path.join(DATA_DIR, "store_layout.csv")
MOVEMENTS_PATH = os.path.join(DATA_DIR, "movements.csv")
ONLINE_PERFORMANCE_PATH = os.path.join(DATA_DIR, "online_performance.csv")
FINAL_INSIGHTS_FILE_PATH = os.path.join(INSIGHTS_DIR, "final_product_insights.csv")
RELOCATION_PLAN_PATH = os.path.join(INSIGHTS_DIR, "relocation_plan.csv")
DECISION_LOG_PATH = os.path.join(AGENT_MEMORY_DIR, "decision_log.json") # Renamed for clarity

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INSIGHTS_DIR, exist_ok=True)
os.makedirs(AGENT_MEMORY_DIR, exist_ok=True)


# --- Helper Functions for Data Loading ---

def _load_df(file_path):
    """General helper to load a DataFrame from a given CSV file path."""
    print(f"DEBUG: Attempting to load file: {file_path}")
    if not os.path.exists(file_path):
        print(f"ERROR: File NOT FOUND at expected path: {file_path}")
        return pd.DataFrame() # Return empty DataFrame if file doesn't exist

    if os.path.getsize(file_path) == 0:
        print(f"Warning: File is empty: {file_path}")
        return pd.DataFrame() # Return empty DataFrame if file is empty

    try:
        df = pd.read_csv(file_path)
        print(f"DEBUG: Successfully loaded {file_path}. Shape: {df.shape}")
        if df.empty:
            print(f"DEBUG: DataFrame loaded from {file_path} is empty.")
        else:
            print(f"DEBUG: First 2 rows of {file_path}:\n{df.head(2)}")
        return df
    except pd.errors.EmptyDataError:
        print(f"Warning: No columns to parse from file {file_path}. It might be empty or just headers.")
        return pd.DataFrame()
    except Exception as e:
        print(f"ERROR: Exception while loading {file_path}: {e}")
        return pd.DataFrame()


# --- Global DataFrames loaded once for tool consistency ---
_final_insights_df = _load_df(FINAL_INSIGHTS_FILE_PATH)
_relocation_plan_df = _load_df(RELOCATION_PLAN_PATH)


def _load_final_insights_df():
    """Returns the in-memory final product insights DataFrame."""
    global _final_insights_df
    if _final_insights_df is None or _final_insights_df.empty:
        _final_insights_df = _load_df(FINAL_INSIGHTS_FILE_PATH)
    return _final_insights_df

def _load_relocation_plan_df():
    """Returns the in-memory relocation plan DataFrame."""
    global _relocation_plan_df
    if _relocation_plan_df is None or _relocation_plan_df.empty:
        _relocation_plan_df = _load_df(RELOCATION_PLAN_PATH)
    return _relocation_plan_df


# --- Agent Memory Management ---

def _load_decision_log():
    """Loads the agent's decision log from JSON."""
    os.makedirs(os.path.dirname(DECISION_LOG_PATH), exist_ok=True) # Ensure directory exists
    
    # Check if the file exists AND is not empty (important for JSON loading)
    if os.path.exists(DECISION_LOG_PATH) and os.path.getsize(DECISION_LOG_PATH) > 0:
        with open(DECISION_LOG_PATH, 'r') as f:
            try:
                data = json.load(f)
                print(f"DEBUG: Successfully loaded decision log from {DECISION_LOG_PATH}. Entries: {len(data)}")
                return data
            except json.JSONDecodeError:
                print(f"Warning: {DECISION_LOG_PATH} is corrupted or empty. Starting with empty memory.")
                return []
    print(f"DEBUG: Decision log file not found or empty at {DECISION_LOG_PATH}. Starting with empty memory.")
    return []

def _save_decision_log(log_data):
    """Saves the agent's decision log to JSON."""
    os.makedirs(os.path.dirname(DECISION_LOG_PATH), exist_ok=True)
    try:
        with open(DECISION_LOG_PATH, 'w') as f:
            json.dump(log_data, f, indent=4)
        print(f"DEBUG: Successfully saved decision log to {DECISION_LOG_PATH}. Entries: {len(log_data)}")
    except Exception as e:
        print(f"ERROR: Failed to save decision log to {DECISION_LOG_PATH}: {e}")


# --- ShelfSense Tools ---

@tool
def get_zone_performance(zone_id: str) -> str:
    """
    Provides detailed performance metrics for a specific store zone (e.g., 'A1', 'B5').
    Includes products in zone, total visits, online views of products, and zone category (Hot/Cold).
    """
    print(f"DEBUG: get_zone_performance called for zone_id: {zone_id}")
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."
    
    zone_data = df[df['Zone'].str.upper() == zone_id.upper()]
    
    if zone_data.empty:
        return f"No data found for zone '{zone_id}'. Please provide a valid zone ID (e.g., 'A1')."
    
    zone_category = zone_data['Zone_Category'].iloc[0]
    total_zone_visits = zone_data['Visits'].sum()
    
    products_in_zone = zone_data[['Product_Name', 'Visits', 'Online_Views']].to_dict(orient='records')
    
    response = (
        f"Zone {zone_id.upper()} is categorized as **{zone_category}** "
        f"with a total of **{total_zone_visits} in-store visits**."
    )
    response += "\nProducts in this zone:\n"
    for prod in products_in_zone:
        response += f"- {prod['Product_Name']} (In-store visits: {prod['Visits']}, Online views: {prod['Online_Views']})\n"
    
    print(f"DEBUG: get_zone_performance response: {response[:100]}...") # Print a snippet
    return response.strip()

@tool
def get_product_insights(product_name: str) -> str:
    """
    Provides detailed insights for a specific product, including its current zone,
    in-store visits, online views, and if it's part of a relocation plan.
    """
    print(f"DEBUG: get_product_insights called for product_name: {product_name}")
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."

    # Use .str.contains for flexible matching, but guide LLM to be precise
    product_data = df[df['Product_Name'].str.contains(product_name, case=False, na=False)]

    if product_data.empty:
        return f"No data found for product '{product_name}'. Please provide a valid product name."

    # If multiple products match (e.g., "juice" matches "Apple Juice", "Orange Juice")
    if len(product_data) > 1:
        match_list = ", ".join(product_data['Product_Name'].tolist())
        return f"Multiple products match '{product_name}'. Please be more specific. Matches: {match_list}"

    product_row = product_data.iloc[0]

    response = (
        f"Product: {product_row['Product_Name']}\n"
        f"Current Zone: {product_row['Zone']} ({product_row['Zone_Category']})\n"
        f"In-store Visits: {product_row['Visits']}\n"
        f"Online Views: {product_row['Online_Views']}\n"
    )

    if pd.notna(product_row['New_Zone']) and product_row['New_Zone'] != product_row['Zone']:
        response += f"This product is recommended for relocation to: {product_row['New_Zone']} (Replacing: {product_row['Old_Product_Name']})\n"
    else:
        response += "This product is not currently part of a recommended relocation plan.\n"

    print(f"DEBUG: get_product_insights response: {response[:150]}...") # Print a snippet
    return response.strip()

@tool
def get_relocation_plan_summary() -> str:
    """
    Provides a summary of the recommended product relocation plan,
    listing products to be moved, their old and new zones, and the products they will replace.
    """
    print("DEBUG: get_relocation_plan_summary called.")
    try:
        # CORRECTED: Load directly from relocation_plan.csv
        df = _load_relocation_plan_df() # Use the specific helper for relocation_plan.csv
    except Exception as e:
        print(f"ERROR: Exception in get_relocation_plan_summary while loading: {e}")
        return f"Error loading relocation data: {e}"

    if df.empty:
        print("DEBUG: Relocation DataFrame is empty after loading.")
        return "Relocation plan is empty."

    # The relocation_plan.csv already contains only the items to be moved,
    # so filtering by 'New_Zone'.notna() might be redundant but harmless here.
    # It ensures that only valid relocation entries are considered.
    relocation_df = df[df['New_Zone'].notna()]

    if relocation_df.empty:
        print("DEBUG: Filtered relocation_df is empty, no current recommendations.")
        return "There are no current product relocation recommendations."

    response = "Current Product Relocation Recommendations:\n"
    for index, row in relocation_df.iterrows():
        response += (
            f"- Move '{row['Product_Name']}' (currently in {row['Current_Zone']}) " # Use 'Current_Zone'
            f"to {row['New_Zone']} (replacing '{row['Old_Product_Name']}')\n"
        )
    print(f"DEBUG: get_relocation_plan_summary response: {response[:200]}...") # Print a snippet
    return response.strip()

@tool
def get_hot_cold_zones() -> str:
    """
    Identifies and lists all 'Hot' (high traffic) and 'Cold' (low traffic) zones in the store.
    """
    print("DEBUG: get_hot_cold_zones called.")
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."

    hot_zones = df[df['Zone_Category'] == 'Hot']['Zone'].unique().tolist()
    cold_zones = df[df['Zone_Category'] == 'Cold']['Zone'].unique().tolist()

    response = "Store Zone Categories:\n"
    if hot_zones:
        response += f"Hot Zones (High Traffic): {', '.join(sorted(hot_zones))}\n"
    else:
        response += "No Hot Zones identified.\n"

    if cold_zones:
        response += f"Cold Zones (Low Traffic): {', '.join(sorted(cold_zones))}\n"
    else:
        response += "No Cold Zones identified.\n"

    print(f"DEBUG: get_hot_cold_zones response: {response[:150]}...") # Print a snippet
    return response.strip()

@tool
def get_past_relocation_outcomes(product_name: str = None) -> str:
    """
    Retrieves recorded outcomes of past product relocations from the agent's memory (decision_log.json).
    Can retrieve all outcomes or filter by a specific product name.

    Args:
        product_name (str, optional): The name of the product whose past relocation outcomes are sought.
                                      If None, all recorded outcomes are returned.
    """
    print(f"DEBUG: get_past_relocation_outcomes called for product_name: {product_name}")
    decision_log = _load_decision_log()
    if not decision_log:
        return "Agent memory is empty. No past relocation outcomes have been recorded yet."

    relevant_outcomes = []
    if product_name:
        relevant_outcomes = [
            entry for entry in decision_log
            if entry['product_name'].lower() == product_name.lower()
        ]
        if not relevant_outcomes:
            return f"No past relocation outcomes found for product '{product_name}' in agent memory."
        response_parts = [f"Past relocation outcomes for {product_name}:"]
    else:
        relevant_outcomes = decision_log
        response_parts = ["All past relocation outcomes:"]


    for outcome in relevant_outcomes:
        response_parts.append(
            f"- On {outcome['timestamp'][:10]}, {outcome['product_name']} was moved from "
            f"{outcome['old_zone']} to {outcome['new_zone']}. Outcome: {outcome['outcome_description']}."
        )
    
    response = "\n".join(response_parts)
    print(f"DEBUG: get_past_relocation_outcomes response: {response[:200]}...") # Print a snippet
    return response

@tool
def record_relocation_outcome(product_name: str, old_zone: str, new_zone: str, outcome_description: str) -> str:
    """
    Records the outcome of a product relocation decision in the agent's memory.
    This helps the agent learn from past actions and reflect on their impact.

    Args:
        product_name (str): The name of the product that was relocated (e.g., 'Dettol').
        old_zone (str): The original zone ID of the product (e.g., 'A1').
        new_zone (str): The new zone ID where the product was moved (e.g., 'B5').
        outcome_description (str): A clear description of the outcome (e.g., 'sales increased by 15%', 'customer complaints reduced by 5%', 'no significant change').
    """
    print(f"DEBUG: record_relocation_outcome called for {product_name} from {old_zone} to {new_zone}.")
    try:
        current_log = _load_decision_log()
        
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "product_name": product_name,
            "old_zone": old_zone,
            "new_zone": new_zone,
            "outcome_description": outcome_description
        }
        
        current_log.append(new_entry)
        _save_decision_log(current_log)
        
        response = f"Successfully recorded relocation outcome for {product_name} from {old_zone} to {new_zone}. Simulated Impact: This data will help ShelfSense provide more accurate future recommendations."
        print(f"DEBUG: record_relocation_outcome success: {response}")
        return response
    except Exception as e:
        print(f"ERROR: Failed to record relocation outcome: {e}")
        return f"Failed to record relocation outcome due to an error: {e}"


@tool
def explain_relocation_reason(product_name: str) -> str:
    """Explains why a product is or isn't scheduled for relocation."""
    print(f"DEBUG: explain_relocation_reason called for {product_name}")

    insights_df = _load_final_insights_df()
    if insights_df.empty:
        return "Final insights data not available. Please ensure final_insights.py has been run."

    product_df = insights_df[insights_df['Product_Name'].str.contains(product_name, case=False, na=False)]
    if product_df.empty:
        return f"No data found for product '{product_name}'. Please provide a valid product name."
    if len(product_df) > 1:
        matches = ", ".join(product_df['Product_Name'].tolist())
        return f"Multiple products match '{product_name}'. Please be more specific. Matches: {matches}"

    product_row = product_df.iloc[0]
    prod_name = product_row['Product_Name']
    current_zone = product_row['Zone']
    current_cat = product_row['Zone_Category']
    visits = int(product_row['Visits'])
    online_views = int(product_row['Online_Views'])

    relocation_df = _load_relocation_plan_df()
    relocation_match = relocation_df[relocation_df['Product_Name'].str.contains(product_name, case=False, na=False)] if not relocation_df.empty else pd.DataFrame()

    if relocation_match.empty:
        return (
            f"{prod_name} is not in the relocation plan. It is in zone {current_zone} "
            f"({current_cat.lower()}), has {online_views} online views and {visits} in-store visits, "
            "and may benefit from future relocation."
        )

    rel_row = relocation_match.iloc[0]
    new_zone = rel_row['New_Zone']
    replaced_product = rel_row['Old_Product_Name']

    new_zone_info = insights_df[insights_df['Zone'] == new_zone].iloc[0]
    new_cat = new_zone_info['Zone_Category']
    new_visits = int(new_zone_info['Visits'])

    reason = (
        f"{prod_name} will move from {current_zone} ({current_cat.lower()}) to {new_zone} "
        f"({new_cat.lower()}) replacing {replaced_product}. It currently receives {visits} visits "
        f"with {online_views} online views, while the target zone sees {new_visits} visits. "
        "Relocating aims to capitalize on higher foot traffic and convert online interest into sales."
    )
    return reason


@tool
def run_store_layout_optimizer() -> str:
    """Generate an optimized layout using movement, sales and online data."""
    try:
        from layout_optimizer import optimize_store_layout
        df = optimize_store_layout()
        if df.empty:
            return "No layout suggestions were generated."
        return (
            f"Created {len(df)} layout suggestions. "
            f"Results saved to {os.path.join('insights', 'optimized_layout.csv')}"
        )
    except Exception as e:
        return f"Failed to optimize layout: {e}"
