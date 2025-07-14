import pandas as pd
import os

LAYOUT_PATH = os.path.join('Data', 'store_layout.csv')
POS_SALES_PATH = os.path.join('data', 'pos_sales.csv')


def calculate_revenue_per_sqft():
    if not os.path.exists(LAYOUT_PATH) or not os.path.exists(POS_SALES_PATH):
        return pd.DataFrame()
    layout = pd.read_csv(LAYOUT_PATH)
    sales = pd.read_csv(POS_SALES_PATH)
    layout['Width'] = 1
    layout['Height'] = 1
    area = layout['Width'] * layout['Height']
    zone_sales = sales.groupby('Zone')['Sales'].sum()
    layout['Sales'] = layout['Zone'].map(zone_sales).fillna(0)
    layout['Revenue_per_sqft'] = layout['Sales'] / area
    return layout[['Zone', 'Revenue_per_sqft']]


if __name__ == '__main__':
    df = calculate_revenue_per_sqft()
    if df.empty:
        print('Missing layout or sales data')
    else:
        print(df.head())
