import pandas as pd
import os

PAIR_PATH = os.path.join('data', 'product_pairs.csv')


def get_complementary(product_name: str):
    if not os.path.exists(PAIR_PATH):
        return []
    df = pd.read_csv(PAIR_PATH)
    matches = df[df['Product'].str.contains(product_name, case=False, na=False)]
    return matches['Complementary'].tolist()


if __name__ == '__main__':
    print(get_complementary('Sugar'))
