import pandas as pd
import os

os.makedirs("insights", exist_ok=True)

try:
    final_insights_df = pd.read_csv("insights/final_product_insights.csv")
    print("Loaded insights/final_product_insights.csv")
except FileNotFoundError:
    print("Error: insights/final_product_insights.csv not found. Please run final_insights.py first.")
    exit()

HIGH_ONLINE_VIEWS_THRESHOLD = 2500 

cold_zone_high_online_hits_df = final_insights_df[
    (final_insights_df["Zone_Category"] == "Cold") &
    (final_insights_df["Online_Views"] >= HIGH_ONLINE_VIEWS_THRESHOLD)
]

print(f"\nIdentified products popular online (views >= {HIGH_ONLINE_VIEWS_THRESHOLD}) but stuck in cold store zones:\n")

if not cold_zone_high_online_hits_df.empty:

    print(cold_zone_high_online_hits_df[[
        "Product_Name", "Zone", "Visits", "Online_Views", "Zone_Category"
    ]].sort_values(by="Online_Views", ascending=False).head(10)) 
else:
    print("No products found matching the criteria (cold zone & high online views).")
    print("Consider adjusting HIGH_ONLINE_VIEWS_THRESHOLD or simulating more diverse data.")


cold_zone_high_online_hits_df.to_csv("insights/recommend_relocation.csv", index=False)
print("\nSaved relocation suggestions for these products to insights/recommend_relocation.csv")