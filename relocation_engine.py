import pandas as pd
import os

# Define file paths
INSIGHTS_DIR = "insights"

FINAL_INSIGHTS_FILE_PATH = os.path.join(INSIGHTS_DIR, "final_product_insights.csv")
RELOCATION_PLAN_PATH = os.path.join(INSIGHTS_DIR, "relocation_plan.csv")

# Ensure insights directory exists
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

def generate_relocation_plan():
    print("Generating smart relocation plan...")

    # Load the final product insights
    final_insights_df = _load_df(FINAL_INSIGHTS_FILE_PATH)

    if final_insights_df.empty:
        print("Error: Final product insights data not available. Cannot generate relocation plan.")
        # Create an empty relocation_plan.csv if the source is empty
        pd.DataFrame(columns=['Product_ID', 'Product_Name', 'Current_Zone', 'Online_Views', 'Visits', 'Zone_Category', 'New_Zone', 'Old_Product_Name']).to_csv(RELOCATION_PLAN_PATH, index=False)
        print("Empty relocation plan created.")
        return

    # Identify potential candidates for relocation
    # Criteria for 'Cold Zone, High Online Views' products (potential to move TO hot zones)
    # Define "High Online Views" relative to other products
    # Define "Low In-store Visits" relative to other products
    # Using quartiles for thresholds to make it dynamic
    
    if final_insights_df['Online_Views'].sum() == 0 and final_insights_df['Visits'].sum() == 0:
        print("No online views or in-store visits data to analyze for relocation.")
        pd.DataFrame(columns=['Product_ID', 'Product_Name', 'Current_Zone', 'Online_Views', 'Visits', 'Zone_Category', 'New_Zone', 'Old_Product_Name']).to_csv(RELOCATION_PLAN_PATH, index=False)
        print("Empty relocation plan created.")
        return

    # Set thresholds dynamically or use fixed ones if preferred
    online_views_threshold = final_insights_df['Online_Views'].quantile(0.75) if not final_insights_df.empty else 0
    visits_threshold_cold = final_insights_df['Visits'].quantile(0.25) if not final_insights_df.empty else 0
    visits_threshold_hot = final_insights_df['Visits'].quantile(0.75) if not final_insights_df.empty else 0

    print(f"DEBUG: Online views threshold (top 25%): {online_views_threshold}")
    print(f"DEBUG: Visits threshold for 'Cold' products (bottom 25%): {visits_threshold_cold}")
    print(f"DEBUG: Visits threshold for 'Hot' products (top 25%): {visits_threshold_hot}")


    # Products to move FROM (Cold Zone, High Online Views, Low In-store Visits)
    candidates_to_move = final_insights_df[
        (final_insights_df['Zone_Category'] == 'Cold') &
        (final_insights_df['Online_Views'] >= online_views_threshold) &
        (final_insights_df['Visits'] <= visits_threshold_cold)
    ].sort_values(by=['Online_Views'], ascending=False)

    # Products to replace (Hot Zone, Low Online Views, High In-store Visits)
    candidates_to_replace = final_insights_df[
        (final_insights_df['Zone_Category'] == 'Hot') &
        (final_insights_df['Online_Views'] <= final_insights_df['Online_Views'].quantile(0.25)) & # Low online views
        (final_insights_df['Visits'] >= visits_threshold_hot) # Still in a hot zone with decent visits
    ].sort_values(by=['Online_Views'], ascending=True)

    print(f"DEBUG: Candidates to move (Cold, High Online, Low Visits):\n{candidates_to_move[['Product_Name', 'Zone', 'Online_Views', 'Visits']]}")
    print(f"DEBUG: Candidates to replace (Hot, Low Online, High Visits):\n{candidates_to_replace[['Product_Name', 'Zone', 'Online_Views', 'Visits']]}")

    relocation_plan = []
    
    # Iterate and match candidates for relocation
    for i in range(min(len(candidates_to_move), len(candidates_to_replace))):
        product_to_move = candidates_to_move.iloc[i]
        product_to_replace = candidates_to_replace.iloc[i]

        relocation_plan.append({
            'Product_ID': product_to_move['Product_ID'],
            'Product_Name': product_to_move['Product_Name'],
            'Current_Zone': product_to_move['Zone'],
            'Online_Views': product_to_move['Online_Views'],
            'Visits': product_to_move['Visits'],
            'Zone_Category': product_to_move['Zone_Category'], # Should be 'Cold'
            'New_Zone': product_to_replace['Zone'], # Move to the hot zone
            'Old_Product_Name': product_to_replace['Product_Name'] # Replace the low-performing hot zone product
        })
        
        # Update final_insights_df in memory for the moved product (optional, but good for consistency)
        # This is where the New_Zone and Old_Product_Name columns get populated for the *moved* product
        final_insights_df.loc[final_insights_df['Product_ID'] == product_to_move['Product_ID'], 'New_Zone'] = product_to_replace['Zone']
        final_insights_df.loc[final_insights_df['Product_ID'] == product_to_move['Product_ID'], 'Old_Product_Name'] = product_to_replace['Product_Name']
        
        # Optionally, remove the replaced product from the insights if it's considered "gone" from the hot zone
        # For simplicity, we just mark it as replaced. The agent can still query its old data.

    relocation_df = pd.DataFrame(relocation_plan)

    if not relocation_df.empty:
        relocation_df.to_csv(RELOCATION_PLAN_PATH, index=False)
        print(f"Smart relocation plan generated and saved to {RELOCATION_PLAN_PATH}")
        print("Relocation Plan:")
        print(relocation_df)
    else:
        # Ensure an empty CSV is created if no recommendations are found
        pd.DataFrame(columns=['Product_ID', 'Product_Name', 'Current_Zone', 'Online_Views', 'Visits', 'Zone_Category', 'New_Zone', 'Old_Product_Name']).to_csv(RELOCATION_PLAN_PATH, index=False)
        print("No relocation plan generated. This might be due to insufficient candidates in either category.")


if __name__ == "__main__":
    generate_relocation_plan()