# final_insights.py
import pandas as pd
import os

# Ensure the 'insights' directory exists
os.makedirs("insights", exist_ok=True)

# Load the in-store product visit data
try:
    zone_product_visits_df = pd.read_csv("insights/zone_product_visits.csv")
    print("Loaded insights/zone_product_visits.csv")
except FileNotFoundError:
    print("Error: insights/zone_product_visits.csv not found. Please run product_visit_analysis.py first.")
    exit()

# Load the online product performance data
try:
    online_product_performance_df = pd.read_csv("data/online_product_performance.csv")
    print("Loaded data/online_product_performance.csv")
except FileNotFoundError:
    print("Error: data/online_product_performance.csv not found. Please run online_data.py first.")
    exit()

# Merge the two DataFrames
# We merge on Product_ID and Product_Name to link the in-store data with online data
final_insights_df = pd.merge(
    zone_product_visits_df,
    online_product_performance_df,
    on=["Product_ID", "Product_Name"],
    how="left" # Use left join to keep all in-store data, filling NaN for unmatched online data
)

# Handle cases where some products might not have online data (shouldn't happen with our simulation, but good practice)
final_insights_df["Online_Views"] = final_insights_df["Online_Views"].fillna(0).astype(int)

# Reorder columns for better readability (optional)
final_insights_df = final_insights_df[[
    "Zone", "Product_ID", "Product_Name", "Visits", "Online_Views", "Zone_Category"
]]

# Save the final merged insights
final_insights_df.to_csv("insights/final_product_insights.csv", index=False)

print("\nGenerated insights/final_product_insights.csv with combined in-store and online data.")
print("\nSample of final_product_insights.csv:")
print(final_insights_df.head())