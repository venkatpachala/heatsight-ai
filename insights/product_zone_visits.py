# product_visit_analysis.py
import pandas as pd
import os

# Ensure the 'insights' directory exists
os.makedirs("insights", exist_ok=True)

# Load the movement data
try:
    movement_df = pd.read_csv("data/movements.csv")
    print("Loaded data/movements.csv")
except FileNotFoundError:
    print("Error: data/movements.csv not found. Please run movements.py first.")
    exit()

# Load the store layout data to get Product_ID and Product_Name per Zone
try:
    layout_df = pd.read_csv("data/store_layout.csv")
    print("Loaded data/store_layout.csv")
except FileNotFoundError:
    print("Error: data/store_layout.csv not found. Please run store_layout.py first.")
    exit()

# 1. Calculate Zone Visit Counts (Visits)
# Count how many times each zone appears in the movement data.
# This represents the total "visits" or "dwell time units" in a zone.
zone_visits = movement_df["Zone"].value_counts().reset_index()
zone_visits.columns = ["Zone", "Visits"]

print("\nCalculated total visits per zone:")
print(zone_visits.head())

# 2. Categorize Zones as 'Hot' or 'Cold'
# We'll use the median number of visits as a threshold to categorize zones.
# Zones with visits >= median are 'Hot', otherwise 'Cold'.
median_visits = zone_visits["Visits"].median()
print(f"\nMedian visits across all zones: {median_visits}")

zone_visits["Zone_Category"] = zone_visits["Visits"].apply(
    lambda x: "Hot" if x >= median_visits else "Cold"
)

print("\nZones categorized as Hot/Cold:")
print(zone_visits.head())

# 3. Merge with Product Information from layout_df
# We need to link the visit counts and category back to the specific products in each zone.
# First, ensure layout_df has only relevant columns if needed, then merge.
# The `layout_df` already contains 'Zone', 'Product_ID', 'Product_Name'.
# We merge `zone_visits` (which has 'Zone', 'Visits', 'Zone_Category') with `layout_df`.
final_zone_product_df = pd.merge(layout_df, zone_visits, on="Zone", how="left")

# Handle zones that might not have been visited at all (fillna with 0 visits and 'Cold')
final_zone_product_df["Visits"] = final_zone_product_df["Visits"].fillna(0).astype(int)
# If a zone has 0 visits, it's definitively cold
final_zone_product_df["Zone_Category"] = final_zone_product_df.apply(
    lambda row: "Cold" if row["Visits"] == 0 else row["Zone_Category"], axis=1
)


# Reorder columns for clarity
final_zone_product_df = final_zone_product_df[[
    "Zone", "Product_ID", "Product_Name", "Visits", "Zone_Category"
]]

# Save the final DataFrame
final_zone_product_df.to_csv("insights/zone_product_visits.csv", index=False)

print("\nGenerated insights/zone_product_visits.csv with product visit counts and zone categories.")
print("\nSample of final_zone_product_df:")
print(final_zone_product_df.head())