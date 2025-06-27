import pandas as pd
import random
rows = ['A', 'B', 'C', 'D', 'E']
cols = range(1, 6)

zones = [f"{row}{col}" for row in rows for col in cols]
product_names = [
    "Coca Cola 500ml", "Lays Chips", "Dove Shampoo", "Parle-G Biscuits", "Maggi Noodles",
    "Tata Salt", "Colgate Paste", "Kissan Jam", "Surf Excel", "Good Day Cookies",
    "Pepsi", "Kurkure", "Dettol", "Ariel", "Pears Soap",
    "Tide", "Amul Butter", "Boost", "Horlicks", "Nestle Milk",
    "Bru Coffee", "Bournvita", "Sunfeast Pasta", "Knorr Soup", "Tropicana Juice"
]

random.shuffle(product_names)

layout_data = {
    "Zone": zones,
    "Product_ID": [f"P{str(i+1).zfill(3)}" for i in range(25)],
    "Product_Name": product_names
}

df = pd.DataFrame(layout_data)
df.to_csv("data/store_layout.csv", index=False)

print("Done")
