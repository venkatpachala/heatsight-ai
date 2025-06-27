import pandas as pd

df = pd.read_csv("insights/final_product_insights.csv")

print("\nDataset Loaded — Shape:", df.shape)

print("\nZone Categories Count:")
print(df["Zone_Category"].value_counts())

print("\nCold Zone + Online Hits (>1000 Views):")
cold_hits = df[(df["Zone_Category"] == "Cold") & (df["Online_Views"] > 1000)]
print(cold_hits[["Product_Name", "Zone", "Visits", "Online_Views"]])

print("\nHot Zone Underperformers (Visits < 15, Online Views < 1000):")
bad_hot = df[(df["Zone_Category"] == "Hot") & (df["Visits"] < 15) & (df["Online_Views"] < 1000)]
print(bad_hot[["Product_Name", "Zone", "Visits", "Online_Views"]])

print("\nCold Hits Found:", len(cold_hits))
print("Hot Underperformers Found:", len(bad_hot))
