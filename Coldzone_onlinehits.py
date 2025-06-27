import pandas as pd

final_df = pd.read_csv("insights/final_product_insights.csv")

cold_online_hits = final_df[
    (final_df["Zone_Category"] == "Cold") &
    (final_df["Online_Views"] > 1000)
]

print("Products popular online but stuck in cold store zones:\n")
print(cold_online_hits[["Product_Name", "Zone", "Visits", "Online_Views"]])

cold_online_hits.to_csv("insights/recommend_relocation.csv", index=False)
print("\nSaved relocation suggestions to insights/recommend_relocation.csv")
