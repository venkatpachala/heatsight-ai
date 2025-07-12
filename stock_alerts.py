import pandas as pd
import numpy as np
import os

STOCK_LEVELS_PATH = os.path.join('data', 'stock_levels.csv')
ALERTS_PATH = os.path.join('insights', 'stock_alerts.csv')


def generate_stock_alerts(threshold: int = 10):
    """Generate stock depletion alerts based on simulated stock levels."""
    if not os.path.exists(STOCK_LEVELS_PATH):
        layout_df = pd.read_csv('Data/store_layout.csv')
        stock_df = pd.DataFrame({
            'Product_ID': layout_df['Product_ID'],
            'Product_Name': layout_df['Product_Name'],
            'Stock': np.random.randint(5, 50, len(layout_df))
        })
        stock_df.to_csv(STOCK_LEVELS_PATH, index=False)
    else:
        stock_df = pd.read_csv(STOCK_LEVELS_PATH)

    low_stock = stock_df[stock_df['Stock'] <= threshold]
    low_stock.to_csv(ALERTS_PATH, index=False)
    print(f'Stock alerts saved to {ALERTS_PATH}')
    return low_stock


if __name__ == '__main__':
    generate_stock_alerts()
