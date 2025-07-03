# relocation_engine.py
import pandas as pd
import os

# Ensure the 'insights' directory exists
os.makedirs("insights", exist_ok=True)

# Load the final merged insights data
try:
    final_insights_df = pd.read_csv("insights/final_product_insights.csv")
    print("Loaded insights/final_product_insights.csv for relocation planning.")
except FileNotFoundError:
    print("Error: insights/final_product_insights.csv not found. Please run final_insights.py first.")
    exit()

# Define criteria for products to be moved TO a better zone (Cold Zone, High Online Views)
# Using the same threshold as cold_zone_onlinehits.py for consistency
HIGH_ONLINE_VIEWS_THRESHOLD = 2500 

cold_zone_candidates_to_move_in = final_insights_df[
    (final_insights_df["Zone_Category"] == "Cold") &
    (final_insights_df["Online_Views"] >= HIGH_ONLINE_VIEWS_THRESHOLD)
].sort_values(by="Online_Views", ascending=False) # Sort by highest online views first

# Define criteria for products to be moved OUT of a hot zone (Hot Zone, Low In-Store Visits)
# We'll use the 25th percentile of visits in hot zones to define "low performing" in hot zones
# This makes the threshold dynamic based on your simulated data
if not final_insights_df[final_insights_df["Zone_Category"] == "Hot"].empty:
    LOW_VISITS_IN_HOT_THRESHOLD = final_insights_df[
        final_insights_df["Zone_Category"] == "Hot"
    ]["Visits"].quantile(0.25) # 25th percentile of visits for hot zones
else:
    LOW_VISITS_IN_HOT_THRESHOLD = 20 # Fallback if no hot zones (unlikely)

hot_zone_candidates_to_move_out = final_insights_df[
    (final_insights_df["Zone_Category"] == "Hot") &
    (final_insights_df["Visits"] <= LOW_VISITS_IN_HOT_THRESHOLD)
].sort_values(by="Visits", ascending=True) # Sort by lowest visits first

print(f"\nCandidates to move IN (Cold Zone, High Online Views): {len(cold_zone_candidates_to_move_in)} products")
if not cold_zone_candidates_to_move_in.empty:
    print(cold_zone_candidates_to_move_in[["Product_Name", "Zone", "Online_Views", "Visits"]].head())

print(f"\nCandidates to move OUT (Hot Zone, Low In-Store Visits): {len(hot_zone_candidates_to_move_out)} products")
if not hot_zone_candidates_to_move_out.empty:
    print(hot_zone_candidates_to_move_out[["Product_Name", "Zone", "Online_Views", "Visits"]].head())


relocation_plan = []

# Pair cold zone candidates with hot zone candidates for relocation
# We'll try to pair one-to-one as long as we have both types of candidates
num_relocations = min(len(cold_zone_candidates_to_move_in), len(hot_zone_candidates_to_move_out))

for i in range(num_relocations):
    cold_product = cold_zone_candidates_to_move_in.iloc[i]
    hot_product = hot_zone_candidates_to_move_out.iloc[i]

    relocation_plan.append({
        "Product_To_Move_In": cold_product["Product_Name"],
        "Current_Cold_Zone": cold_product["Zone"],
        "Cold_Zone_Visits": cold_product["Visits"],
        "Cold_Product_Online_Views": cold_product["Online_Views"],
        
        "Product_To_Move_Out": hot_product["Product_Name"],
        "Current_Hot_Zone": hot_product["Zone"],
        "Hot_Zone_Visits": hot_product["Visits"],
        "Hot_Product_Online_Views": hot_product["Online_Views"],
        
        "Suggested_New_Zone_For_Move_In": hot_product["Zone"], # Suggest moving into the hot zone
        "Reason": "High online demand, low in-store visibility. Move to high traffic zone occupied by underperforming product."
    })

relocation_df = pd.DataFrame(relocation_plan)

# Save the smart relocation plan
relocation_df.to_csv("insights/relocation_plan.csv", index=False)

print("\nSmart relocation plan generated and saved to insights/relocation_plan.csv")
if not relocation_df.empty:
    print("\nSample Relocation Plan:")
    print(relocation_df.head())
else:
    print("No relocation plan generated. This might be due to insufficient candidates in either category.")