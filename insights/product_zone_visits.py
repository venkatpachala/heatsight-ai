import pandas as pd
import os


layout_df = pd.read_csv("data/store_layout.csv")
movement_df = pd.read_csv("data/movements.csv")

zone_visits = movement_df["Zone"].value_counts().reset_index()
zone_visits.columns = ["Zone", "Visits"]

merged_df = pd.merge(layout_df, zone_visits, on="Zone", how="left")
merged_df["Visits"] = merged_df["Visits"].fillna(0).astype(int)
merged_df = merged_df.sort_values(by="Visits", ascending=False)

os.makedirs("insights", exist_ok=True)
merged_df.to_csv("insights/zone_product_visits.csv", index=False)

def label_zone(visits):
    if visits > 25:
        return "Hot"
    elif visits >= 10:
        return "Warm"
    else:
        return "Cold"

merged_df["Zone_Category"] = merged_df["Visits"].apply(label_zone)

# Save updated CSV
merged_df.to_csv("insights/zone_product_visits.csv", index=False)

print("Merged zone + product + visit data saved to insights/zone_product_visits.csv")
