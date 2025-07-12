import pandas as pd
import os
from heatsight_tools import _load_final_insights_df

OPTIMIZED_LAYOUT_PATH = os.path.join('insights', 'optimized_layout.csv')


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


if __name__ == '__main__':
    optimize_layout()
