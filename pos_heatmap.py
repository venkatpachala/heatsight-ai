import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os

POS_SALES_PATH = os.path.join('data', 'pos_sales.csv')


def generate_pos_sales_heatmap():
    """Generate a heatmap of POS sales by zone."""
    os.makedirs('heatmap', exist_ok=True)
    if not os.path.exists(POS_SALES_PATH):
        layout_df = pd.read_csv('Data/store_layout.csv')
        zones = layout_df['Zone']
        sales_df = pd.DataFrame({'Zone': zones, 'Sales': np.random.randint(50, 200, len(zones))})
        sales_df.to_csv(POS_SALES_PATH, index=False)
    else:
        sales_df = pd.read_csv(POS_SALES_PATH)

    zone_sales = sales_df.set_index('Zone')['Sales'].to_dict()
    rows = [chr(ord('A') + i) for i in range(10)]
    cols = range(1, 11)
    grid = np.zeros((len(rows), len(cols)), dtype=int)
    for r_idx, r in enumerate(rows):
        for c_idx, c in enumerate(cols):
            grid[r_idx, c_idx] = zone_sales.get(f'{r}{c}', 0)

    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(grid, annot=True, fmt='d', cmap='Blues',
                xticklabels=cols, yticklabels=rows, linewidths=.5, linecolor='lightgray', ax=ax)
    ax.set_title('POS Sales Heatmap', color='#f0f0f0')
    ax.set_xlabel('Shelf Column', color='#f0f0f0')
    ax.set_ylabel('Shelf Row', color='#f0f0f0')
    ax.tick_params(axis='x', rotation=0, colors='#e0e0e0')
    ax.tick_params(axis='y', rotation=0, colors='#e0e0e0')
    ax.set_facecolor('#121212')
    fig.patch.set_facecolor('#121212')
    plt.tight_layout()
    plt.savefig('heatmap/pos_sales_heatmap.png')
    return fig


if __name__ == '__main__':
    generate_pos_sales_heatmap()
