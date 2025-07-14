import pandas as pd
import os

ALERTS_PATH = os.path.join('data', 'alerts_log.json')


def suggest_actions():
    if not os.path.exists(ALERTS_PATH):
        return []
    alerts = pd.read_json(ALERTS_PATH)
    suggestions = []
    for _, row in alerts.iterrows():
        if row.get('issue') == 'Stockout':
            suggestions.append(f"Consider moving stock to zone {row['zone']} to cover shortage")
    return suggestions


if __name__ == '__main__':
    for s in suggest_actions():
        print('-', s)
