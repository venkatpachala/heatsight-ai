import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = "Data"
INSIGHTS_DIR = "insights"
MEMORY_PATH = os.path.join("agent_memory", "relocation_memory.json")
POS_SALES_PATH = os.path.join("data", "pos_sales.csv")

os.makedirs(INSIGHTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)

# helper to load CSV

def _load_csv(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def _load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _normalize(series):
    if series.empty:
        return series
    min_v = series.min()
    max_v = series.max()
    if max_v - min_v == 0:
        return series.apply(lambda x: 0.0)
    return (series - min_v) / (max_v - min_v)

def generate_relocation_scores():
    layout_df = _load_csv(os.path.join(DATA_DIR, "store_layout.csv"))
    movements_df = _load_csv(os.path.join(DATA_DIR, "movements.csv"))
    online_df = _load_csv(os.path.join(DATA_DIR, "online_product_performance.csv"))
    final_df = _load_csv(os.path.join(INSIGHTS_DIR, "final_product_insights.csv"))

    if layout_df.empty or final_df.empty:
        print("Required data missing. Run store_layout.py and Final_insights.py first.")
        return pd.DataFrame()

    if movements_df.empty:
        movements_df = pd.DataFrame({"Zone": layout_df["Zone"], "Visits": 0})
    footfall = movements_df["Zone"].value_counts().to_dict()

    # POS sales
    if not os.path.exists(POS_SALES_PATH):
        # create simple random sales if missing
        zones = layout_df["Zone"]
        sales_df = pd.DataFrame({"Zone": zones, "Sales": np.random.randint(50, 200, len(zones))})
        os.makedirs(os.path.dirname(POS_SALES_PATH), exist_ok=True)
        sales_df.to_csv(POS_SALES_PATH, index=False)
    sales_df = _load_csv(POS_SALES_PATH)
    zone_sales = sales_df.set_index("Zone")["Sales"].to_dict()

    # Merge basic info
    df = final_df.merge(online_df, on=["Product_ID", "Product_Name"], how="left")
    df["Online_Views_y"].fillna(0, inplace=True)
    df.rename(columns={"Online_Views_x": "Online_Views"}, inplace=True)
    df["Footfall"] = df["Zone"].map(footfall).fillna(0)
    df["Zone_Sales"] = df["Zone"].map(zone_sales).fillna(0)
    df["Conversion"] = df.apply(lambda r: r["Zone_Sales"] / r["Footfall"] if r["Footfall"] > 0 else 0, axis=1)

    # scoring
    df["footfall_score"] = _normalize(df["Footfall"])
    df["pos_score"] = _normalize(df["Zone_Sales"])
    df["online_score"] = _normalize(df["Online_Views"])
    df["velocity_score"] = df["pos_score"]
    df["conversion_score"] = _normalize(df["Conversion"])
    df["cold_zone_bonus"] = df["Zone_Category"].apply(lambda x: 1 if str(x).lower() == "cold" else 0)

    memory = _load_json(MEMORY_PATH)
    recent_products = {m.get("product_id") for m in memory if m.get("timestamp")}
    df["relocation_penalty"] = df["Product_ID"].apply(lambda x: -1 if x in recent_products else 0)

    df["seasonal_match"] = 0
    df["complementary_bonus"] = 0
    df["price_visibility_boost"] = 0
    df["ab_test_bonus"] = 0

    df["Relocation_Score"] = (
        0.15 * df["footfall_score"] +
        0.15 * df["pos_score"] +
        0.15 * df["online_score"] +
        0.10 * df["velocity_score"] +
        0.10 * df["conversion_score"] +
        0.10 * df["cold_zone_bonus"] +
        0.05 * df["relocation_penalty"] +
        0.05 * df["seasonal_match"] +
        0.05 * df["complementary_bonus"] +
        0.05 * df["price_visibility_boost"] +
        0.05 * df["ab_test_bonus"]
    ) * 100

    # zone scoring for suggestions
    zone_df = pd.DataFrame({
        "Zone": layout_df["Zone"],
        "footfall": [footfall.get(z, 0) for z in layout_df["Zone"]],
        "sales": [zone_sales.get(z, 0) for z in layout_df["Zone"]],
    })
    zone_df["score"] = _normalize(zone_df["footfall"]) * 0.6 + _normalize(zone_df["sales"]) * 0.4

    def suggest_zone(current_zone):
        if zone_df.empty:
            return current_zone
        best = zone_df.sort_values("score", ascending=False)["Zone"].tolist()
        for z in best:
            if z != current_zone:
                return z
        return current_zone

    df["Suggested_Zone"] = df["Zone"].apply(suggest_zone)

    def explain(row):
        contributions = {
            "footfall": 0.15 * row["footfall_score"],
            "pos": 0.15 * row["pos_score"],
            "online": 0.15 * row["online_score"],
            "velocity": 0.10 * row["velocity_score"],
            "conversion": 0.10 * row["conversion_score"],
            "cold_zone": 0.10 * row["cold_zone_bonus"],
        }
        top = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3]
        parts = []
        for k, v in top:
            if k == "footfall":
                parts.append(f"footfall {int(row['Footfall'])}")
            elif k == "pos":
                parts.append(f"POS sales {int(row['Zone_Sales'])}")
            elif k == "online":
                parts.append(f"online views {int(row['Online_Views'])}")
            elif k == "velocity":
                parts.append(f"sales velocity {int(row['Zone_Sales'])}")
            elif k == "conversion":
                parts.append(f"conversion {row['Conversion']:.2f}")
            elif k == "cold_zone":
                parts.append("in cold zone")
        return ", ".join(parts)

    df["Why_This_Zone"] = df.apply(explain, axis=1)

    output_cols = [
        "Product_ID", "Product_Name", "Zone", "Suggested_Zone", "Relocation_Score", "Why_This_Zone"
    ]
    result = df[output_cols].rename(columns={"Zone": "Current_Zone"})
    result.to_csv(os.path.join(INSIGHTS_DIR, "relocation_intelligence.csv"), index=False)
    return result

if __name__ == "__main__":
    generate_relocation_scores()
