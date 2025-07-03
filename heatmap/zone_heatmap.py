# zone_Heatmap.py
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np

# Ensure the 'heatmap' directory exists
os.makedirs("heatmap", exist_ok=True)

# Load the movement data
try:
    movement_df = pd.read_csv("data/movements.csv")
    print("Loaded data/movements.csv for heatmap generation.")
except FileNotFoundError:
    print("Error: data/movements.csv not found. Please run movements.py first.")
    exit()

# 1. Count visits per zone
zone_counts = movement_df["Zone"].value_counts().to_dict()

# 2. Define the 10x10 grid structure
rows = [chr(ord('A') + i) for i in range(10)] # A, B, ..., J
cols = range(1, 11) # 1, 2, ..., 10

# 3. Populate the heatmap grid
# Initialize a 10x10 numpy array with zeros
heatmap_grid = np.zeros((len(rows), len(cols)), dtype=int)

for r_idx, row_label in enumerate(rows):
    for c_idx, col_label in enumerate(cols):
        zone_name = f"{row_label}{col_label}"
        heatmap_grid[r_idx, c_idx] = zone_counts.get(zone_name, 0)

print("\nPopulated heatmap grid with zone visit counts.")
print("Sample of heatmap_grid (top-left 5x5):")
print(heatmap_grid[:5, :5])


# 4. Create the heatmap visualization
plt.figure(figsize=(12, 10)) # Adjust figure size for a 10x10 grid
sns.heatmap(heatmap_grid, annot=True, fmt="d", cmap="YlOrRd",
            xticklabels=cols, yticklabels=rows, linewidths=.5, linecolor='lightgray')

plt.title("🛍️ Heatmap of In-Store Zone Visits (Customer Movement)", fontsize=16)
plt.xlabel("Shelf Column", fontsize=12)
plt.ylabel("Shelf Row", fontsize=12)
plt.xticks(rotation=0) # Keep column labels horizontal
plt.yticks(rotation=0) # Keep row labels horizontal
plt.tight_layout() # Adjust layout to prevent labels from overlapping

# Save the heatmap image
plt.savefig("heatmap/zone_heatmap.png")
plt.show()

print("\nIn-store Heatmap generated and saved to heatmap/zone_heatmap.png")