import pandas as pd
import numpy as np
import os
from heatsight_tools import _load_final_insights_df

SEASONAL_PLAN_PATH = os.path.join('insights', 'seasonal_plan.csv')


def generate_seasonal_plan(season: str = 'winter'):
    """Generate a simplistic seasonal relocation plan based on online views."""
    df = _load_final_insights_df()
    if df.empty:
        print('Final insights unavailable. Seasonal plan not generated.')
        pd.DataFrame().to_csv(SEASONAL_PLAN_PATH, index=False)
        return

    df = df.copy()
    # Simulate seasonal demand multiplier
    np.random.seed(0)
    df['Seasonal_Demand'] = (df['Online_Views'] * np.random.uniform(0.8, 1.2, len(df))).astype(int)
    df = df.sort_values('Seasonal_Demand', ascending=False)

    hot_zones = df[df['Zone_Category'] == 'Hot']['Zone'].unique().tolist()
    plan = []
    hot_index = 0
    for _, row in df.iterrows():
        if row['Zone_Category'] == 'Cold' and hot_zones:
            plan.append({
                'Product_ID': row['Product_ID'],
                'Product_Name': row['Product_Name'],
                'Current_Zone': row['Zone'],
                'Target_Zone': hot_zones[hot_index % len(hot_zones)],
                'Seasonal_Demand': row['Seasonal_Demand']
            })
            hot_index += 1

    pd.DataFrame(plan).to_csv(SEASONAL_PLAN_PATH, index=False)
    print(f'Seasonal plan saved to {SEASONAL_PLAN_PATH}')


if __name__ == '__main__':
    generate_seasonal_plan()
