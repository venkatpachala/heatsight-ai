# movements.py
import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Ensure the 'data' directory exists, though it should from store_layout.py
os.makedirs("data", exist_ok=True)

# Load the store layout to get available zones
try:
    layout_df = pd.read_csv("data/store_layout.csv")
    zones = layout_df["Zone"].tolist()
except FileNotFoundError:
    print("Error: data/store_layout.csv not found. Please run store_layout.py first.")
    exit()

num_customers = 200 # Increased number of customers for a larger store
# Each customer will visit a random number of zones
min_movements_per_customer = 10
max_movements_per_customer = 30 
movement_data = []

# Define a base start time for the simulation
base_start_time = datetime(2025, 7, 3, 9, 0, 0) # Today's date, 9 AM

for i in range(num_customers):
    customer_id = f"C{str(i+1).zfill(4)}" # Padded to 4 digits for more customers
    num_movements = random.randint(min_movements_per_customer, max_movements_per_customer)
    
    # Each customer starts their shopping trip at a slightly different time
    start_time_offset_minutes = random.randint(0, 180) # Customers arrive within a 3-hour window
    customer_start_time = base_start_time + timedelta(minutes=start_time_offset_minutes)
    
    # Ensure customers don't always visit the same zones; sample with replacement if num_movements > len(zones)
    # Using random.choices for flexibility in choosing zones multiple times
    # Prioritize some zones over others (e.g., entrance, popular categories)
    # For now, let's keep it simple with random sampling
    visited_zones = random.sample(zones, min(num_movements, len(zones)))
    if num_movements > len(zones):
        # If a customer has more movements than unique zones, they might revisit zones
        extra_visits = random.choices(zones, k=(num_movements - len(zones)))
        visited_zones.extend(extra_visits)
    
    random.shuffle(visited_zones) # Shuffle the sequence of visits for diversity

    current_timestamp = customer_start_time
    for j, zone in enumerate(visited_zones):
        # Simulate time spent in a zone or moving between zones
        time_spent_seconds = random.randint(15, 90) # Spend 15 seconds to 1.5 minutes per zone
        
        movement_data.append({
            "Customer_ID": customer_id,
            "Timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Zone": zone
        })
        
        current_timestamp += timedelta(seconds=time_spent_seconds)

movement_df = pd.DataFrame(movement_data)

# Save the DataFrame to CSV
movement_df.to_csv("data/movements.csv", index=False)

print(f"Generated data/movements.csv with {len(movement_df)} customer movement records for {num_customers} customers.")