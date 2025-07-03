# store_layout.py
import pandas as pd
import random
import os

# Define the grid dimensions for a 10x10 store
rows = [chr(ord('A') + i) for i in range(10)] # A, B, C, D, E, F, G, H, I, J
cols = range(1, 11) # Columns 1 to 10

# Generate zone names (e.g., A1, A2, ..., J10)
zones = [f"{row}{col}" for row in rows for col in cols]
num_zones = len(zones)

# Define a much larger and more diverse list of Walmart-like product names
# Mixture of groceries, electronics, apparel, home goods, health/beauty, etc.
product_names = [
    # Groceries (Packaged)
    "Coca Cola 2L", "Lays Chips Family", "Parle-G Biscuits Pack", "Maggi Noodles 6-Pack", "Tata Salt 1kg",
    "Colgate Toothpaste 150g", "Kissan Mixed Fruit Jam", "Surf Excel Detergent 1kg", "Good Day Cashew Cookies", "Pepsi 1.5L",
    "Kurkure Masala Munch", "Ariel Laundry Pods", "Amul Butter 500g", "Boost Health Drink", "Horlicks Classic",
    "Nescafe Classic Coffee 100g", "Bournvita 500g", "Sunfeast Yippee Noodles", "Knorr Tomato Soup", "Tropicana Orange Juice 1L",
    "Britannia Good Day Butter", "Frooti Mango Drink 1L", "Bingo Mad Angles", "KitKat Chocolate Bar", "Cadbury Dairy Milk 100g",
    "Dabur Honey 500g", "Patanjali Atta 5kg", "Fortune Refined Oil 1L", "MDH Chana Masala", "Everest Garam Masala",
    "Sugar 1kg", "Rice Basmati 5kg", "Wheat Flour 10kg", "Dal Arhar 1kg", "Tea Powder 500g",
    "Corn Flakes 500g", "Oats 1kg", "Peanut Butter 500g", "Jaggery 500g", "Vinegar 500ml",

    # Fresh Produce/Dairy (Simulated)
    "Fresh Apples 1kg", "Bananas Dozen", "Onions 1kg", "Potatoes 1kg", "Tomatoes 500g",
    "Amul Milk 1L Pouch", "Curd 400g", "Paneer 200g", "Eggs 6-pack", "Bread Loaf Brown",

    # Health & Beauty
    "Dove Shampoo 180ml", "Dettol Antiseptic Liquid", "Pears Transparent Soap", "Lux Jasmine Soap", "Close-up Toothpaste Gel",
    "Lifebuoy Total Soap", "Clinic Plus Shampoo", "Whisper Sanitary Pads", "Vim Dishwash Liquid", "Lizol Floor Cleaner 1L",
    "Fair & Lovely Cream", "Nivea Body Lotion", "Garnier Face Wash", "Himalaya Neem Face Pack", "Head & Shoulders Shampoo",
    "Vaseline Intensive Care", "Ponds Cold Cream", "Listerine Mouthwash", "Oral-B Toothbrush", "Godrej No.1 Soap",

    # Home Goods & Electronics
    "Duracell AA Batteries 4-pack", "Philips LED Bulb", "Prestige Pressure Cooker 3L", "Hawkins Cooker 5L", "Bajaj Mixer Grinder",
    "Iron Box Philips", "Ceiling Fan Usha", "Extension Board 6-socket", "Smart LED TV 32inch", "Bluetooth Speaker JBL",
    "Headphones Boat", "Power Bank MI", "USB Cable Charger", "Laptop Bag", "Printer Ink Cartridge",

    # Apparel & Footwear (Generic)
    "Men's T-Shirt Basic", "Women's Jeans Denim", "Kids' School Uniform", "Socks Multi-pack", "Sport Shoes Adidas",
    "Sandals Bata", "Formal Shirt Men", "Ethnic Kurti Women", "Baby Romper", "Underwear Multi-pack",

    # Toys & Stationary
    "Hot Wheels Car Set", "Barbie Doll", "Lego Classic Box", "Cricket Bat Kids", "Football Size 5",
    "Notebook A4 200 pages", "Pens Blue Pack", "Pencil Box", "Crayons Set", "Eraser Pack",

    # Pet Supplies
    "Pedigree Dog Food 1kg", "Whiskas Cat Food 500g", "Dog Leash", "Cat Litter 5kg", "Bird Seed 1kg",

    # Automotive & Hardware
    "Engine Oil 1L", "Car Cleaning Kit", "Screwdriver Set", "Hammer 500g", "Tape Measure 5m",

    # Pharmacy (OTC - Over the Counter)
    "Paracetamol Tablets", "Band-Aid Strips", "Vicks VapoRub", "Digestive Tablets", "Antacid Liquid"
]


# Ensure we have at least as many unique products as zones
if len(product_names) < num_zones:
    # If not enough products, extend by sampling existing ones
    product_names.extend(random.sample(product_names, num_zones - len(product_names)))
elif len(product_names) > num_zones:
    # If more products than zones, truncate the list
    product_names = product_names[:num_zones]

random.shuffle(product_names) # Shuffle to assign products randomly to zones

# Create the layout data
layout_data = {
    "Zone": zones,
    "Product_ID": [f"P{str(i+1).zfill(3)}" for i in range(num_zones)], # Ensures unique product IDs
    "Product_Name": product_names
}

df_layout = pd.DataFrame(layout_data)

# Ensure the 'data' directory exists
os.makedirs("data", exist_ok=True)

# Save the DataFrame to CSV
df_layout.to_csv("data/store_layout.csv", index=False)

print(f"Generated data/store_layout.csv with {num_zones} store zones (10x10 grid) and diverse product assignments.")