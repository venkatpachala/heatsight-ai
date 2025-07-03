# online_data.py
import pandas as pd
import random
import os

# Ensure the 'data' directory exists
os.makedirs("data", exist_ok=True)

# Load the store layout to get Product_ID and Product_Name
try:
    layout_df = pd.read_csv("data/store_layout.csv")
    print("Loaded data/store_layout.csv for online data simulation.")
except FileNotFoundError:
    print("Error: data/store_layout.csv not found. Please run store_layout.py first.")
    exit()

# Simulate online views for each product
# We'll use two ranges to create a mix of moderately popular and very popular items
online_views = []
for _ in range(len(layout_df)):
    # 70% chance of being in the lower-mid range, 30% chance of being in the higher range
    if random.random() < 0.7:
        online_views.append(random.randint(500, 2000))  # Moderately popular
    else:
        online_views.append(random.randint(2500, 8000)) # Very popular / Trending

layout_df["Online_Views"] = online_views

# Select only the relevant columns for online performance data
online_performance_df = layout_df[["Product_ID", "Product_Name", "Online_Views"]]

# Save the DataFrame to CSV
online_performance_df.to_csv("data/online_product_performance.csv", index=False)

print("\nGenerated data/online_product_performance.csv with simulated online product views.")
print("\nSample of online_product_performance.csv:")
print(online_performance_df.head())