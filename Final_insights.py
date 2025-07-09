import pandas as pd
import os

# Define file paths
DATA_DIR = "data"
INSIGHTS_DIR = "insights"

STORE_LAYOUT_PATH = os.path.join(DATA_DIR, "store_layout.csv")
MOVEMENTS_PATH = os.path.join(DATA_DIR, "movements.csv")
ONLINE_PERFORMANCE_PATH = os.path.join(DATA_DIR, "online_product_performance.csv")
FINAL_INSIGHTS_FILE_PATH = os.path.join(INSIGHTS_DIR, "final_product_insights.csv")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(INSIGHTS_DIR, exist_ok=True)

def _load_df(file_path):
    """Helper to load CSV, returning empty DataFrame if file is missing or empty."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print(f"Warning: {file_path} not found or is empty.")
        return pd.DataFrame()
    try:
        return pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        print(f"Warning: {file_path} is an empty CSV file.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def generate_final_insights():
    print("Generating final product insights...")

    # Load data
    store_layout_df = _load_df(STORE_LAYOUT_PATH)
    movements_df = _load_df(MOVEMENTS_PATH)
    online_performance_df = _load_df(ONLINE_PERFORMANCE_PATH)

    if store_layout_df.empty:
        print("Error: store_layout.csv is empty or missing. Cannot generate insights.")
        return
    if movements_df.empty:
        print("Warning: movements.csv is empty or missing. Zone categories and visits might be inaccurate.")
    if online_performance_df.empty:
        print("Warning: online_product_performance.csv is empty or missing. Online views will be N/A.")

    # 1. Calculate Zone Visits and Category
    if not movements_df.empty:
        zone_visits = movements_df.groupby('Zone').size().reset_index(name='Visits')
    else:
        zone_visits = pd.DataFrame(columns=['Zone', 'Visits']) # Empty if no movements

    # Determine Zone Category based on visits (simple threshold)
    # Get all unique zones from store_layout to ensure all zones are covered
    all_zones = store_layout_df[['Zone']].drop_duplicates()
    zone_data = pd.merge(all_zones, zone_visits, on='Zone', how='left')
    zone_data['Visits'] = zone_data['Visits'].fillna(0) # Fill NaN visits with 0

    # Define 'Hot' and 'Cold' zones - adjust threshold as needed for your data
    # Calculate median or average visits to set a dynamic threshold
    if not zone_data.empty and zone_data['Visits'].sum() > 0:
        threshold = zone_data['Visits'].mean() # Using mean as a simple threshold
        zone_data['Zone_Category'] = zone_data['Visits'].apply(lambda x: 'Hot' if x >= threshold else 'Cold')
        print(f"DEBUG: Zone categories calculated with threshold (mean visits): {threshold}")
        print(zone_data[['Zone', 'Visits', 'Zone_Category']].head()) # Debugging
    else:
        zone_data['Zone_Category'] = 'Unknown' # Default if no movement data

    # 2. Merge all data
    # Merge store layout with online performance first
    # Ensure 'Product_ID' and 'Product_Name' are correctly matched
    if not online_performance_df.empty:
        merged_df = pd.merge(store_layout_df, online_performance_df, on=['Product_ID', 'Product_Name'], how='left')
    else:
        merged_df = store_layout_df.copy() # Start with store layout if no online data
        merged_df['Online_Views'] = 0 # Default online views to 0

    # Merge with zone data to add Visits and Zone_Category
    final_insights_df = pd.merge(merged_df, zone_data[['Zone', 'Visits', 'Zone_Category']], on='Zone', how='left')

    # Fill NaN values for Visits and Online_Views if they don't exist
    final_insights_df['Visits'] = final_insights_df['Visits'].fillna(0).astype(int)
    final_insights_df['Online_Views'] = final_insights_df['Online_Views'].fillna(0).astype(int)
    final_insights_df['Zone_Category'] = final_insights_df['Zone_Category'].fillna('Unknown') # Default unknown zones

    # Add 'New_Zone' and 'Old_Product_Name' columns if they don't exist
    # These columns are primarily populated by relocation_engine.py, but final_insights.py should create them
    if 'New_Zone' not in final_insights_df.columns:
        final_insights_df['New_Zone'] = ''
    if 'Old_Product_Name' not in final_insights_df.columns:
        final_insights_df['Old_Product_Name'] = ''

    # Save the final insights
    final_insights_df.to_csv(FINAL_INSIGHTS_FILE_PATH, index=False)
    print(f"Final product insights saved to {FINAL_INSIGHTS_FILE_PATH}")
    print(f"DEBUG: Columns in final_product_insights.csv: {final_insights_df.columns.tolist()}") # Debugging
    print(f"DEBUG: Head of final_product_insights.csv:\n{final_insights_df.head()}") # Debugging

if __name__ == "__main__":
    generate_final_insights()