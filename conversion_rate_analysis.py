import pandas as pd
import os

MOVEMENTS_PATH = os.path.join('data', 'movements.csv')
POS_SALES_PATH = os.path.join('data', 'pos_sales.csv')


def calculate_zone_conversion_rates():
    if not os.path.exists(MOVEMENTS_PATH) or not os.path.exists(POS_SALES_PATH):
        return pd.DataFrame()
    move_df = pd.read_csv(MOVEMENTS_PATH)
    sales_df = pd.read_csv(POS_SALES_PATH)
    visits = move_df['Zone'].value_counts().rename('Visits')
    sales = sales_df.groupby('Zone')['Sales'].sum()
    df = pd.concat([visits, sales], axis=1).fillna(0)
    df['Conversion_Rate'] = df['Sales'] / df['Visits'].replace(0, 1)
    return df.reset_index().rename(columns={'index': 'Zone'})


if __name__ == '__main__':
    result = calculate_zone_conversion_rates()
    if result.empty:
        print('Required data not found')
    else:
        print(result)
