import os
import json
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
from heatsight_tools import _load_final_insights_df

OPTIMIZED_LAYOUT_PATH = os.path.join('insights', 'optimized_layout.csv')

# Path for caching past relocations
RELOCATION_MEMORY_PATH = 'relocation_memory.json'

# Data directories may vary in casing across platforms
DATA_DIRS = ['data', 'Data']


def _find_data_file(filename: str) -> str:
    """Return the first existing path for filename in known data dirs."""
    for d in DATA_DIRS:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    # default to first dir
    return os.path.join(DATA_DIRS[0], filename)


def optimize_layout():
    """Greedy layout optimizer assigning top products to highest traffic zones."""
    df = _load_final_insights_df()
    if df.empty:
        print('Final insights unavailable. Layout not optimized.')
        pd.DataFrame().to_csv(OPTIMIZED_LAYOUT_PATH, index=False)
        return

    product_df = df.sort_values(['Online_Views', 'Visits'], ascending=False).reset_index(drop=True)
    zones_sorted = df.sort_values('Visits', ascending=False)['Zone'].unique().tolist()

    layout = []
    for idx, row in product_df.iterrows():
        target_zone = zones_sorted[idx % len(zones_sorted)]
        layout.append({'Zone': target_zone, 'Product_ID': row['Product_ID'], 'Product_Name': row['Product_Name']})

    pd.DataFrame(layout).to_csv(OPTIMIZED_LAYOUT_PATH, index=False)
    print(f'Optimized layout saved to {OPTIMIZED_LAYOUT_PATH}')


def optimize_store_layout(alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2,
                           theta: float = 0.5, delta: float = 0.3, kappa: float = 0.2) -> pd.DataFrame:
    """Smart optimizer combining footfall, POS sales and online interest.

    Returns a DataFrame with suggested product placements sorted by zone desirability."""

    # Load datasets
    final_df = _load_final_insights_df()
    if final_df.empty:
        print('Final product insights unavailable. Cannot optimize layout.')
        return pd.DataFrame()

    movements_path = _find_data_file('movements.csv')
    sales_path = _find_data_file('pos_sales.csv')

    movements_df = pd.read_csv(movements_path) if os.path.exists(movements_path) else pd.DataFrame()

    if os.path.exists(sales_path):
        pos_sales_df = pd.read_csv(sales_path)
    else:
        # create random sales if missing
        layout_zones = final_df['Zone'].unique()
        np.random.seed(0)
        pos_sales_df = pd.DataFrame({'Zone': layout_zones,
                                     'Sales': np.random.randint(50, 200, len(layout_zones))})
        os.makedirs(os.path.dirname(sales_path), exist_ok=True)
        pos_sales_df.to_csv(sales_path, index=False)

    # Compute footfall per zone
    if not movements_df.empty:
        footfall_df = movements_df.groupby('Zone').size().reset_index(name='Footfall')
    else:
        footfall_df = pd.DataFrame({'Zone': final_df['Zone'].unique(), 'Footfall': 0})

    zone_df = pd.merge(pos_sales_df, footfall_df, on='Zone', how='outer').fillna(0)
    zone_df['Conversion_Rate'] = zone_df.apply(
        lambda r: (r['Sales'] / r['Footfall']) if r['Footfall'] else 0,
        axis=1
    )
    zone_df['Zone_Score'] = (
        alpha * zone_df['Footfall'] + beta * zone_df['Sales'] + gamma * zone_df['Conversion_Rate']
    )

    # Map sales to products
    final_df = pd.merge(final_df, zone_df[['Zone', 'Sales']], on='Zone', how='left')
    final_df.rename(columns={'Sales': 'Past_Sales'}, inplace=True)
    final_df['Past_Sales'] = final_df['Past_Sales'].fillna(0)

    # Load relocation memory
    if os.path.exists(RELOCATION_MEMORY_PATH) and os.path.getsize(RELOCATION_MEMORY_PATH) > 0:
        with open(RELOCATION_MEMORY_PATH, 'r') as f:
            relocation_mem: Dict[str, Dict] = json.load(f)
    else:
        relocation_mem = {}

    now = datetime.now()

    def penalty(product_id: str) -> float:
        record = relocation_mem.get(product_id)
        if not record:
            return 0.0
        try:
            last_time = datetime.fromisoformat(record['timestamp'])
            days = (now - last_time).days
        except Exception:
            days = 9999
        return -1.0 / (days + 1)

    final_df['Penalty'] = final_df['Product_ID'].apply(penalty)
    final_df['Product_Score'] = (
        theta * final_df['Online_Views'] +
        delta * final_df['Past_Sales'] +
        kappa * final_df['Penalty']
    )

    zones_sorted = zone_df.sort_values('Zone_Score', ascending=False).reset_index(drop=True)
    products_sorted = final_df.sort_values('Product_Score', ascending=False).reset_index(drop=True)

    assignments = []

    for _, zone_row in zones_sorted.iterrows():
        if products_sorted.empty:
            break
        for idx, prod_row in products_sorted.iterrows():
            pid = prod_row['Product_ID']
            mem_rec = relocation_mem.get(pid, {})
            if mem_rec.get('zone') == zone_row['Zone']:
                continue  # avoid repeating the same suggestion

            days_since = 9999
            if 'timestamp' in mem_rec:
                try:
                    days_since = (now - datetime.fromisoformat(mem_rec['timestamp'])).days
                except Exception:
                    days_since = 9999

            if days_since < 7 and prod_row['Past_Sales'] >= mem_rec.get('sales', 0) * 0.5:
                continue

            explanation = (
                f"Zone score {zone_row['Zone_Score']:.2f} (footfall {zone_row['Footfall']}, "
                f"sales {zone_row['Sales']}) matches product score {prod_row['Product_Score']:.2f}."
            )

            assignments.append({
                'Zone': zone_row['Zone'],
                'Product_ID': pid,
                'Product_Name': prod_row['Product_Name'],
                'Why_This_Zone': explanation
            })

            relocation_mem[pid] = {
                'zone': zone_row['Zone'],
                'timestamp': now.isoformat(),
                'sales': zone_row['Sales']
            }

            products_sorted = products_sorted.drop(idx).reset_index(drop=True)
            break

    with open(RELOCATION_MEMORY_PATH, 'w') as f:
        json.dump(relocation_mem, f, indent=4)

    result_df = pd.DataFrame(assignments)
    result_df.to_csv(OPTIMIZED_LAYOUT_PATH, index=False)
    print(f'Smart optimized layout saved to {OPTIMIZED_LAYOUT_PATH}')
    return result_df


if __name__ == '__main__':
    optimize_store_layout()
