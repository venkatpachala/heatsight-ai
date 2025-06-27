import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

movement_df = pd.read_csv("data/movements.csv")
zone_counts = movement_df["Zone"].value_counts().to_dict()

rows = ['A', 'B', 'C', 'D', 'E']
cols = ['1', '2', '3', '4', '5']

heatmap_grid = []

for row in rows:
    heatmap_row = []
    for col in cols:
        zone = row + col
        count = zone_counts.get(zone, 0)
        heatmap_row.append(count)
    heatmap_grid.append(heatmap_row)

plt.figure(figsize=(8, 6))
sns.heatmap(heatmap_grid, annot=True, fmt="d", cmap="YlOrRd", xticklabels=cols, yticklabels=rows)
plt.title("🛍️ Heatmap of Zone Visits (Customer Movement)")
plt.xlabel("Shelf Column")
plt.ylabel("Shelf Row")

os.makedirs("heatmap", exist_ok=True)
plt.savefig("heatmap/zone_heatmap.png")
plt.show()

print("Heat Map generated")
