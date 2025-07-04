import pandas as pd
import random
from datetime import datetime, timedelta
import os

os.makedirs("data", exist_ok=True)

try:
    layout_df = pd.read_csv("data/store_layout.csv")
    zones = layout_df["Zone"].tolist()
except FileNotFoundError:
    print("Error: data/store_layout.csv not found. Please run store_layout.py first.")
    exit()

num_customers = 200
min_movements_per_customer = 10
max_movements_per_customer = 30
movement_data = []

base_start_time = datetime(2025, 7, 3, 9, 0, 0)

for i in range(num_customers):
    customer_id = f"C{str(i+1).zfill(4)}"
    num_movements = random.randint(min_movements_per_customer, max_movements_per_customer)
    
    start_time_offset_minutes = random.randint(0, 180)
    customer_start_time = base_start_time + timedelta(minutes=start_time_offset_minutes)
    
    visited_zones = random.sample(zones, min(num_movements, len(zones)))
    if num_movements > len(zones):
        extra_visits = random.choices(zones, k=(num_movements - len(zones)))
        visited_zones.extend(extra_visits)
    
    random.shuffle(visited_zones)

    current_timestamp = customer_start_time
    for j, zone in enumerate(visited_zones):
        time_spent_seconds = random.randint(15, 90)
        
        movement_data.append({
            "Customer_ID": customer_id,
            "Timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Zone": zone
        })
        
        current_timestamp += timedelta(seconds=time_spent_seconds)

movement_df = pd.DataFrame(movement_data)

movement_df.to_csv("data/movements.csv", index=False)

print(f"Generated data/movements.csv with {len(movement_df)} customer movement records for {num_customers} customers.")