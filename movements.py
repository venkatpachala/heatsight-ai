import pandas as pd
import random
from datetime import datetime, timedelta
layout_df = pd.read_csv("data/store_layout.csv")
zones = layout_df["Zone"].tolist()
num_customers = 50
movement_data = []

for i in range(num_customers):
    customer_id = f"C{str(i+1).zfill(3)}"
    num_movements = random.randint(5, 10)
    start_time = datetime(2025, 6, 27, 10, 0, 0) + timedelta(minutes=random.randint(0, 30))
    
    visited_zones = random.sample(zones, num_movements)
    
    for j, zone in enumerate(visited_zones):
        timestamp = start_time + timedelta(seconds=j * random.randint(5, 15))
        movement_data.append({
            "Customer_ID": customer_id,
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Zone": zone
        })

movement_df = pd.DataFrame(movement_data)
movement_df.to_csv("data/movements.csv", index=False)

print("Customer movement data saved to data/movements.csv")


