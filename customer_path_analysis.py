import pandas as pd
import os

JOURNEY_PATH = os.path.join('data', 'customer_journeys.csv')


def common_paths(top_n=5):
    if not os.path.exists(JOURNEY_PATH):
        return []
    df = pd.read_csv(JOURNEY_PATH)
    counts = df['Path'].value_counts().head(top_n)
    return list(zip(counts.index, counts.values))


if __name__ == '__main__':
    print(common_paths())
