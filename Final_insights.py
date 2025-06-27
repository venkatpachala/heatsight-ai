import pandas as pd
import os

zone_df = pd.read_csv("insights/zone_product_visits.csv")
online_df = pd.read_csv("data/online_product_performance.csv")

final_df = pd.merge(zone_df, online_df, on=["Product_ID", "Product_Name"], how="left")

os.makedirs("insights", exist_ok=True)
final_df.to_csv("insights/final_product_insights.csv", index=False)

print("Final merged insights saved to insights/final_product_insights.csv")
