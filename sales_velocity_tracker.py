import pandas as pd
import os

POS_SALES_PATH = os.path.join('data', 'pos_sales.csv')


def identify_declines(window=30, drop_pct=0.2):
    if not os.path.exists(POS_SALES_PATH):
        return pd.DataFrame()
    df = pd.read_csv(POS_SALES_PATH)
    if 'Date' not in df.columns:
        return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'])
    recent = df[df['Date'] >= df['Date'].max() - pd.Timedelta(days=window)]
    baseline = df[df['Date'] < df['Date'].max() - pd.Timedelta(days=window)]
    recent_sales = recent.groupby('Product_ID')['Sales'].sum()
    baseline_sales = baseline.groupby('Product_ID')['Sales'].sum()
    compare = pd.concat([baseline_sales, recent_sales], axis=1, keys=['Baseline','Recent']).fillna(0)
    compare['Decline'] = (compare['Baseline'] - compare['Recent']) / compare['Baseline'].replace(0,1)
    declining = compare[compare['Decline'] > drop_pct]
    return declining.reset_index()


if __name__ == '__main__':
    result = identify_declines()
    if result.empty:
        print('Sales data not sufficient')
    else:
        print(result)
