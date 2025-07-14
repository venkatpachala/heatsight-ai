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
PRODUCT_CATEGORY_MAP_PATH = os.path.join(DATA_DIR, "product_category_map.csv")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INSIGHTS_DIR, exist_ok=True)
os.makedirs(AGENT_MEMORY_DIR, exist_ok=True)


# --- Helper Functions for Data Loading ---

_DATA_CACHE = {}

def _load_df(file_path):
    """General helper to load a DataFrame from a given CSV file path with simple caching."""
    if file_path in _DATA_CACHE:
        return _DATA_CACHE[file_path]

    print(f"DEBUG: Attempting to load file: {file_path}")
    if not os.path.exists(file_path):
        print(f"ERROR: File NOT FOUND at expected path: {file_path}")
        return pd.DataFrame()

    if os.path.getsize(file_path) == 0:
        print(f"Warning: File is empty: {file_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)
        _DATA_CACHE[file_path] = df
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
def get_past_relocation_outcomes(product_name: str = None, zone: str = None) -> str:
    """
    Retrieves recorded outcomes of past product relocations from the agent's memory (decision_log.json).
    Can retrieve all outcomes or filter by a specific product name or zone.

    Args:
        product_name (str, optional): Filter by product name.
        zone (str, optional): Filter by a zone involved in the move (old or new).
    """
    print(f"DEBUG: get_past_relocation_outcomes called for product_name={product_name}, zone={zone}")
    decision_log = _load_decision_log()
    if not decision_log:
        return "Agent memory is empty. No past relocation outcomes have been recorded yet."

    relevant_outcomes = decision_log
    if product_name:
        relevant_outcomes = [entry for entry in relevant_outcomes if entry['product_name'].lower() == product_name.lower()]
    if zone:
        zone_l = zone.lower()
        if zone_l in ("hot", "cold"):
            df = _load_final_insights_df()
            zone_set = set(
                df[df["Zone_Category"].str.lower() == zone_l]["Zone"].str.upper()
            )
            relevant_outcomes = [
                entry
                for entry in relevant_outcomes
                if entry["old_zone"].upper() in zone_set or entry["new_zone"].upper() in zone_set
            ]
        else:
            zone_u = zone.upper()
            relevant_outcomes = [
                entry
                for entry in relevant_outcomes
                if entry["old_zone"].upper() == zone_u or entry["new_zone"].upper() == zone_u
            ]
    if not relevant_outcomes:
        filters = []
        if product_name:
            filters.append(f"product '{product_name}'")
        if zone:
            filters.append(f"zone '{zone}'")
        filt_str = " and ".join(filters) if filters else "the log"
        return f"No past relocation outcomes found for {filt_str}."
    response_parts = ["Past relocation outcomes:"]


    for outcome in relevant_outcomes:
        response_parts.append(
            f"- On {outcome['date']}, {outcome['product_name']} was moved from "
            f"{outcome['old_zone']} to {outcome['new_zone']}. Outcome: {outcome['outcome_description']}.")
    
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
            "product_name": product_name,
            "old_zone": old_zone,
            "new_zone": new_zone,
            "date": datetime.now().date().isoformat(),
            "outcome_description": outcome_description,
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

@tool
def get_relocation_score(product_name: str) -> str:
    """Return the relocation score and suggested zone for a given product."""
    path = os.path.join(INSIGHTS_DIR, "relocation_intelligence.csv")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        df = pd.read_csv(path)
    else:
        try:
            from relocation_intelligence import generate_relocation_scores
            df = generate_relocation_scores()
        except Exception as e:
            return f"Failed to compute relocation score: {e}"
    if df.empty:
        return "Relocation intelligence data is unavailable."
    match = df[df['Product_Name'].str.contains(product_name, case=False, na=False)]
    if match.empty:
        return f"No relocation score found for '{product_name}'."
    row = match.iloc[0]
    return (
        f"{row['Product_Name']} currently in {row['Current_Zone']} has a relocation score of "
        f"{row['Relocation_Score']:.1f}. Suggested zone: {row['Suggested_Zone']}. "
        f"Factors: {row.get('Why_This_Zone', 'N/A')}"
    )

@tool
def get_dwell_time_by_zone() -> str:
    """Compute average dwell time per zone from movement logs."""
    df = _load_df(MOVEMENTS_PATH)
    if df.empty or 'Timestamp' not in df.columns:
        return "Movement data unavailable."
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values(['Customer_ID', 'Timestamp'])
    df['Next_Time'] = df.groupby('Customer_ID')['Timestamp'].shift(-1)
    df['Dwell'] = (df['Next_Time'] - df['Timestamp']).dt.total_seconds()
    dwell = df.groupby('Zone')['Dwell'].mean().dropna()
    if dwell.empty:
        return "Not enough movement data to compute dwell time."
    lines = ["Average dwell time by zone (seconds):"]
    for zone, sec in dwell.sort_values(ascending=False).items():
        lines.append(f"- {zone}: {sec:.1f}")
    return "\n".join(lines)

@tool
def get_conversion_rate_by_zone() -> str:
    """Return conversion rate (sales/visits) for each zone."""
    visits_df = _load_df(MOVEMENTS_PATH)
    sales_df = _load_df(os.path.join(DATA_DIR, 'pos_sales.csv'))
    if visits_df.empty or sales_df.empty:
        return "Movement or sales data unavailable."
    visits = visits_df['Zone'].value_counts()
    result_lines = ["Zone conversion rates:"]
    for _, row in sales_df.iterrows():
        zone = row['Zone']
        sales = row['Sales']
        v = visits.get(zone, 0)
        rate = sales / v if v > 0 else 0
        result_lines.append(f"- {zone}: {rate:.2f}")
    return "\n".join(result_lines)

@tool
def get_sales_velocity(product_name: str) -> str:
    """Estimate sales velocity for a product based on zone sales and visits."""
    insights_df = _load_final_insights_df()
    if insights_df.empty:
        return "Insights data unavailable."
    prod_df = insights_df[insights_df['Product_Name'].str.contains(product_name, case=False, na=False)]
    if prod_df.empty:
        return f"Product '{product_name}' not found."
    row = prod_df.iloc[0]
    zone = row['Zone']
    sales_df = _load_df(os.path.join(DATA_DIR, 'pos_sales.csv'))
    sales = sales_df.loc[sales_df['Zone'] == zone, 'Sales'].sum() if not sales_df.empty else 0
    move_df = _load_df(MOVEMENTS_PATH)
    visits = (move_df['Zone'] == zone).sum() if not move_df.empty else 0
    velocity = sales / visits if visits else sales
    return (
        f"{row['Product_Name']} in zone {zone} has a sales velocity of {velocity:.2f} units per visit "
        f"based on {sales} sales and {visits} visits."
    )

@tool
def get_inventory_reorder_recommendations() -> str:
    """Suggest products that need reordering based on stock levels."""
    stock_path = os.path.join(DATA_DIR, 'stock_levels.csv')
    alert_path = os.path.join('insights', 'stock_alerts.csv')
    stock_df = _load_df(stock_path)
    if stock_df.empty:
        return "Stock level data not available."
    threshold = max(5, int(stock_df['Stock'].quantile(0.25)))
    low_df = stock_df[stock_df['Stock'] <= threshold]
    if low_df.empty:
        return "All products sufficiently stocked."
    low_df.to_csv(alert_path, index=False)
    lines = ["Products needing reorder:"]
    for _, r in low_df.iterrows():
        lines.append(f"- {r['Product_Name']} (stock {r['Stock']})")
    return "\n".join(lines)

@tool
def get_customer_journey_patterns() -> str:
    """Identify common customer paths through the store."""
    df = _load_df(MOVEMENTS_PATH)
    if df.empty:
        return "Movement data unavailable."
    df = df.sort_values(['Customer_ID', 'Timestamp'])
    transitions = df.groupby('Customer_ID')['Zone'].apply(lambda x: list(x))
    pairs = {}
    for path in transitions:
        for i in range(len(path) - 1):
            pair = (path[i], path[i+1])
            pairs[pair] = pairs.get(pair, 0) + 1
    if not pairs:
        return "Not enough data to derive journeys."
    top = sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:5]
    lines = ["Top customer movements:"]
    for (a,b), count in top:
        lines.append(f"- {a} → {b}: {count} times")
    return "\n".join(lines)

@tool
def suggest_seasonal_layout_changes() -> str:
    """Provide seasonal placement suggestions from seasonal_plan.csv."""
    path = os.path.join('insights', 'seasonal_plan.csv')
    df = _load_df(path)
    if df.empty:
        return "Seasonal plan data unavailable."
    lines = ["Seasonal relocation suggestions:"]
    for _, r in df.iterrows():
        lines.append(f"- Move {r['Product_Name']} to {r['Target_Zone']} (demand {r['Seasonal_Demand']})")
    return "\n".join(lines)

@tool
def compare_layout_metrics(before_csv: str, after_csv: str) -> str:
    """Compare zone visit totals before and after a layout change."""
    before = _load_df(before_csv)
    after = _load_df(after_csv)
    if before.empty or after.empty:
        return "One of the layout files is missing or empty."
    diff = after['Visits'].sum() - before['Visits'].sum()
    return f"Total visits changed by {diff}."

@tool
def run_what_if_placement(query: str) -> str:
    """Placeholder for what-if placement simulation."""
    try:
        from layout_optimizer import optimize_store_layout
        df = optimize_store_layout()
        return f"Simulated layout generated with {len(df)} suggestions for query: {query}."
    except Exception as e:
        return f"Simulation failed: {e}"

@tool
def fetch_complementary_products(product_name: str) -> str:
    """Return a list of complementary products that pair well with the given item."""
    df = _load_final_insights_df()
    if df.empty:
        return "Product insights unavailable."
    products = df[df['Product_Name'].str.contains(product_name, case=False, na=False)]
    if products.empty:
        return f"Product '{product_name}' not found."
    all_products = df['Product_Name'].tolist()
    comp = [p for p in all_products if p not in products['Product_Name'].tolist()]
    suggestions = comp[:3]
    return "Complementary items: " + ", ".join(suggestions)

@tool
def get_real_time_placement_recommendation(event_context: str) -> str:
    """Provide a quick placement suggestion based on current context."""
    try:
        from layout_optimizer import optimize_store_layout
        df = optimize_store_layout()
        if df.empty:
            return "No recommendations available right now."
        top = df.iloc[0]
        return (
            f"Move {top['Product_Name']} to {top['Zone']} as a quick win for {event_context}."
        )
    except Exception as e:
        return f"Failed to generate real-time recommendation: {e}"


@tool
def get_zone_conversion_rate() -> str:
    """Return conversion rate per zone using movements and POS sales."""
    from conversion_rate_analysis import calculate_zone_conversion_rates
    df = calculate_zone_conversion_rates()
    if df.empty:
        return "Conversion rate data unavailable."
    lines = ["Zone conversion rates:"]
    for _, r in df.iterrows():
        lines.append(f"- {r['Zone']}: {r['Conversion_Rate']:.2f}")
    return "\n".join(lines)


@tool
def get_declining_products() -> str:
    """List products with declining sales velocity."""
    from sales_velocity_tracker import identify_declines
    df = identify_declines()
    if df.empty:
        return "No significant declines detected."
    lines = ["Products with >20% decline:"]
    for _, r in df.iterrows():
        lines.append(f"- {r['Product_ID']} decline {r['Decline']:.1%}")
    return "\n".join(lines)


@tool
def compare_dwell_time(zone_a: str, zone_b: str) -> str:
    """Compare average dwell time between two zones."""
    if not os.path.exists('data/dwell_time.csv'):
        return "Dwell time data not available."
    df = pd.read_csv('data/dwell_time.csv')
    a = df[df['Zone'] == zone_a]['Avg_Dwell_Time'].mean()
    b = df[df['Zone'] == zone_b]['Avg_Dwell_Time'].mean()
    if pd.isna(a) or pd.isna(b):
        return "One of the zones has no data."
    return f"{zone_a}: {a:.1f}s vs {zone_b}: {b:.1f}s"


@tool
def get_complementary_products(product_name: str) -> str:
    """Return complementary items from product_pairs.csv."""
    from complementary_product_mapper import get_complementary
    comps = get_complementary(product_name)
    if not comps:
        return "No complementary products found."
    return "Complementary items: " + ", ".join(comps)


@tool
def suggest_complementary_pairs() -> str:
    """
    Returns a list of complementary product placement pairs based on category similarity and current location.
    """
    if not os.path.exists(PRODUCT_CATEGORY_MAP_PATH):
        return "Product category mapping file not available."

    df = pd.read_csv(PRODUCT_CATEGORY_MAP_PATH)
    if df.empty:
        return "Product category mapping file not available."

    rules = {
        "Cereal": "Milk",
        "Shampoo": "Conditioner",
        "Chips": "Cold Drinks",
        "Toothpaste": "Toothbrush",
        "Bread": "Butter/Jam",
        "Pasta": "Pasta Sauce",
        "Chocolates": "Gifting Items",
        "Maggi": "Tomato Ketchup",
    }

    suggestions = []
    for cat_a, cat_b in rules.items():
        a_df = df[df["Category"].str.contains(cat_a, case=False, na=False)]
        b_df = df[df["Category"].str.contains(cat_b, case=False, na=False)]
        if a_df.empty or b_df.empty:
            continue
        a_row = a_df.iloc[0]
        b_row = b_df.iloc[0]
        zone_a = str(a_row["Current_Zone"])
        zone_b = str(b_row["Current_Zone"])
        if zone_a and zone_b and zone_a[0] != zone_b[0]:
            suggestions.append(
                f"Consider relocating {a_row['Product_Name']} near {b_row['Product_Name']} (zones {zone_a} & {zone_b})."
            )

    if not suggestions:
        return "No complementary placement suggestions available."

    return "\n".join(suggestions)


@tool
def recommend_product_placement() -> str:
    """Recommend high revenue shelf spaces."""
    from revenue_per_sqft_calculator import calculate_revenue_per_sqft
    df = calculate_revenue_per_sqft()
    if df.empty:
        return "Unable to compute revenue per sqft."
    top = df.sort_values('Revenue_per_sqft', ascending=False).head(3)
    lines = ["Top zones by revenue per sqft:"]
    for _, r in top.iterrows():
        lines.append(f"- {r['Zone']} : {r['Revenue_per_sqft']:.2f}")
    return "\n".join(lines)


@tool
def analyze_restock_needs() -> str:
    """Analyze restock log for recent activity."""
    path = os.path.join('data', 'restock_log.csv')
    if not os.path.exists(path):
        return "Restock log not found."
    df = pd.read_csv(path)
    recent = df.tail(3)
    lines = ["Recent restocks:"]
    for _, r in recent.iterrows():
        lines.append(f"- {r['Product_ID']} at {r['Timestamp']}")
    return "\n".join(lines)


@tool
def get_top_footfall_zones(top_n: int = 5) -> str:
    """Return the zones with the highest customer visits."""
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available."
    visits = df.groupby('Zone')['Visits'].sum().sort_values(ascending=False).head(top_n)
    lines = ["Top zones by footfall:"]
    for zone, v in visits.items():
        lines.append(f"- {zone}: {int(v)} visits")
    return "\n".join(lines)


@tool
def get_low_conversion_hot_zones() -> str:
    """Identify hot zones with many visits but low sales."""
    insights_df = _load_final_insights_df()
    sales_path = os.path.join(DATA_DIR, 'sales_by_hour.csv')
    sales_df = _load_df(sales_path)
    layout_df = _load_df(STORE_LAYOUT_PATH)
    if insights_df.empty or sales_df.empty or layout_df.empty:
        return "Required data unavailable."
    sales_totals = sales_df.groupby('Product_ID')['Sales'].sum().reset_index()
    zone_sales = pd.merge(layout_df, sales_totals, on='Product_ID', how='left').groupby('Zone')['Sales'].sum().fillna(0)
    zone_visits = insights_df.groupby('Zone')['Visits'].sum()
    df = pd.DataFrame({'Visits': zone_visits, 'Sales': zone_sales})
    df['Conversion'] = df['Sales'] / df['Visits'].replace(0, 1)
    hot_zones = insights_df[insights_df['Zone_Category'] == 'Hot']['Zone'].unique()
    low_df = df.loc[hot_zones]
    low_df = low_df[low_df['Conversion'] < 0.3]
    if low_df.empty:
        return "No low conversion hot zones found."
    lines = ["Hot zones with low conversion:"]
    for zone, row in low_df.sort_values('Conversion').iterrows():
        lines.append(f"- {zone}: {int(row['Visits'])} visits, {int(row['Sales'])} sales")
    return "\n".join(lines)


@tool
def get_products_to_relocate(top_n: int = 5) -> str:
    """Products trending online but sitting in cold zones."""
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available."
    cold = df[df['Zone_Category'] == 'Cold']
    cold = cold.sort_values('Online_Views', ascending=False).head(top_n)
    if cold.empty:
        return "No products need relocation."
    lines = ["Trending products in cold zones:"]
    for _, r in cold.iterrows():
        lines.append(f"- {r['Product_Name']} in {r['Zone']} with {int(r['Online_Views'])} views")
    return "\n".join(lines)


@tool
def get_relocation_reason(product_name: str) -> str:
    """Explain why a product should be relocated."""
    return explain_relocation_reason.func(product_name)


@tool
def simulate_relocation_swap(product_a: str, zone_a: str, product_b: str, zone_b: str) -> str:
    """Simulate impact of swapping two products between zones."""
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available."
    a_row = df[df['Product_Name'].str.contains(product_a, case=False, na=False)]
    b_row = df[df['Product_Name'].str.contains(product_b, case=False, na=False)]
    if a_row.empty or b_row.empty:
        return "One of the products not found."
    a_vis = int(a_row.iloc[0]['Visits'])
    b_vis = int(b_row.iloc[0]['Visits'])
    gain_a = b_vis - a_vis
    gain_b = a_vis - b_vis
    return (
        f"Moving {product_a} to {zone_b} could change visits by {gain_a}; "
        f"moving {product_b} to {zone_a} could change visits by {gain_b}."
    )


@tool
def get_high_online_low_pos_products(top_n: int = 5) -> str:
    """Products with high online views but low POS sales."""
    insights_df = _load_final_insights_df()
    sales_path = os.path.join(DATA_DIR, 'sales_by_hour.csv')
    sales_df = _load_df(sales_path)
    layout_df = _load_df(STORE_LAYOUT_PATH)
    if insights_df.empty or sales_df.empty or layout_df.empty:
        return "Required data unavailable."
    sales_totals = sales_df.groupby('Product_ID')['Sales'].sum().reset_index()
    merged = pd.merge(layout_df, sales_totals, on='Product_ID', how='left')
    merged = pd.merge(merged, insights_df[['Product_ID', 'Online_Views']], on='Product_ID', how='left')
    merged['Sales'] = merged['Sales'].fillna(0)
    high_online = merged.sort_values('Online_Views', ascending=False)
    candidates = high_online[high_online['Sales'] < merged['Sales'].quantile(0.3)].head(top_n)
    if candidates.empty:
        return "No such products found."
    lines = ["High online view but low POS sales:"]
    for _, r in candidates.iterrows():
        lines.append(f"- {r['Product_Name']} ({int(r['Online_Views'])} views, {int(r['Sales'])} sales)")
    return "\n".join(lines)


@tool
def get_last_month_relocations() -> str:
    """Retrieve relocation decisions from the last month."""
    log = _load_decision_log()
    if not log:
        return "No relocation history available."
    cutoff = datetime.now() - pd.Timedelta(days=30)
    recent = [d for d in log if datetime.fromisoformat(d['date']) >= cutoff]
    if not recent:
        return "No relocations in the last month."
    lines = ["Relocations in the last month:"]
    for d in recent:
        lines.append(
            f"- {d['product_name']} from {d['old_zone']} to {d['new_zone']} on {d['date']}"
        )
    return "\n".join(lines)


@tool
def recommend_seasonal_plan(festival: str) -> str:
    """Suggest shelf changes for an upcoming event or festival."""
    try:
        from seasonal_planner import generate_seasonal_plan
        generate_seasonal_plan(festival)
        path = os.path.join('insights', 'seasonal_plan.csv')
        df = _load_df(path)
        if df.empty:
            return "Seasonal plan data unavailable."
        top = df.head(5)
        lines = [f"Seasonal plan for {festival}:"]
        for _, r in top.iterrows():
            lines.append(f"- Move {r['Product_Name']} to {r['Target_Zone']} (demand {r['Seasonal_Demand']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to generate seasonal plan: {e}"


@tool
def get_impulse_placement_suggestions(top_n: int = 5) -> str:
    """Recommend products suited for checkout impulse placement."""
    df = _load_final_insights_df()
    if df.empty:
        return "Final insights data not available."
    df = df.sort_values(['Visits', 'Online_Views'], ascending=False).head(top_n)
    lines = ["Impulse placement suggestions:"]
    for _, r in df.iterrows():
        lines.append(f"- {r['Product_Name']}")
    return "\n".join(lines)


@tool
def trigger_stock_alerts() -> str:
    """Trigger stock alerts using stock_alerts module."""
    try:
        from stock_alerts import generate_stock_alerts
        alerts = generate_stock_alerts()
        return f"Generated {len(alerts)} stock alerts." if not alerts.empty else "No alerts."
    except Exception as e:
        return f"Failed to generate alerts: {e}"

