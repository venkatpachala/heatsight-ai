import pandas as pd
import os

df = pd.read_csv("insights/final_product_insights.csv")

cold_hits = df[
    (df["Zone_Category"] == "Cold") & 
    (df["Online_Views"] > 500)
]

bad_hot = df[
    (df["Zone_Category"] == "Hot") & 
    (df["Visits"] < 50) & 
    (df["Online_Views"] < 600)
]


relocation_plan = []

for i in range(min(len(cold_hits), len(bad_hot))):
    cold_row = cold_hits.iloc[i]
    hot_row = bad_hot.iloc[i]

    relocation_plan.append({
        "Product_To_Move": cold_row["Product_Name"],
        "Current_Zone": cold_row["Zone"],
        "Online_Views": cold_row["Online_Views"],
        "Visits": cold_row["Visits"],
        
        "Suggested_Zone": hot_row["Zone"],
        "Replace_Product": hot_row["Product_Name"],
        "Replace_Online_Views": hot_row["Online_Views"],
        "Replace_Visits": hot_row["Visits"],
        
        "Reason": "Cold zone product has high online demand. Hot zone product underperforming."
    })

relocation_df = pd.DataFrame(relocation_plan)
os.makedirs("insights", exist_ok=True)
relocation_df.to_csv("insights/relocation_plan.csv", index=False)

print("Smart relocation plan saved to insights/relocation_plan.csv")
