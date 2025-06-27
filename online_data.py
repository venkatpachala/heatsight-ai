import pandas as pd
import random
import os

layout_df = pd.read_csv("data/store_layout.csv")

layout_df["Online_Views"] = [
    random.choice([
        random.randint(500, 900),     
        random.randint(1200, 2500)    
    ])
    for _ in range(len(layout_df))
]

os.makedirs("data", exist_ok=True)
layout_df[["Product_ID", "Product_Name", "Online_Views"]].to_csv("data/online_product_performance.csv", index=False)

print("Simulated online product views saved to data/online_product_performance.csv")
