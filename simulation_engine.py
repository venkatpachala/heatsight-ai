import os
import numpy as np
import pandas as pd

from heatsight_tools import (
    _load_df,
    _load_final_insights_df,
    STORE_LAYOUT_PATH,
    DATA_DIR,
    premium_products,
)
from conversion_rate_analysis import calculate_zone_conversion_rates


def _ensure_sales_by_zone():
    """Aggregate sales by zone using sales_by_hour and store layout."""
    sales_hour_path = os.path.join(DATA_DIR, "sales_by_hour.csv")
    layout_df = _load_df(STORE_LAYOUT_PATH)
    sales_df = _load_df(sales_hour_path)
    if layout_df.empty:
        return pd.Series(dtype=float)
    if sales_df.empty:
        zones = layout_df["Zone"].unique()
        np.random.seed(0)
        return pd.Series(np.random.randint(50, 200, len(zones)), index=zones)
    prod_sales = sales_df.groupby("Product_ID")["Sales"].sum().reset_index()
    zone_sales = pd.merge(layout_df, prod_sales, on="Product_ID", how="left").groupby("Zone")["Sales"].sum().fillna(0)
    return zone_sales


def _ensure_dwell_time():
    path = os.path.join(DATA_DIR, "dwell_time.csv")
    df = _load_df(path)
    if df.empty:
        return pd.Series(dtype=float)
    return df.set_index("Zone")["Avg_Dwell_Time"]


def run_what_if_placement(product_name: str, new_zone: str) -> dict:
    """Simulate moving a product to a new zone and estimate sales uplift."""
    insights = _load_final_insights_df()
    if insights.empty:
        return {"error": "Insights data unavailable"}

    prod_match = insights[insights["Product_Name"].str.contains(product_name, case=False, na=False)]
    if prod_match.empty:
        return {"error": f"Product '{product_name}' not found"}
    prod_row = prod_match.iloc[0]
    current_zone = prod_row["Zone"]

    visits_by_zone = insights.groupby("Zone")["Visits"].sum()
    visits_current = visits_by_zone.get(current_zone, 0)
    visits_new = visits_by_zone.get(new_zone, visits_by_zone.mean())

    conversion = calculate_zone_conversion_rates()
    if conversion.empty or "Zone" not in conversion.columns:
        conv_dict = {}
    else:
        conv_dict = dict(zip(conversion["Zone"], conversion["Conversion_Rate"]))
    conv_current = conv_dict.get(current_zone, 0)
    conv_new = conv_dict.get(new_zone, conv_current)

    zone_sales = _ensure_sales_by_zone()
    sales_current = zone_sales.get(current_zone, 0)
    sales_new = zone_sales.get(new_zone, sales_current)

    dwell = _ensure_dwell_time()
    dwell_current = dwell.get(current_zone, dwell.mean() if not dwell.empty else 1)
    dwell_new = dwell.get(new_zone, dwell_current)

    footfall_ratio = visits_new / max(visits_current, 1)
    conv_ratio = conv_new / max(conv_current, 0.01)
    dwell_ratio = dwell_new / max(dwell_current, 1)

    entrance_candidates = insights.sort_values("Visits", ascending=False)["Zone"].head(3).str.upper().tolist()
    impulse_bonus = 1.1 if new_zone.upper() in entrance_candidates else 1.0

    base_factor = 0.5 * footfall_ratio + 0.3 * conv_ratio + 0.2 * dwell_ratio
    predicted_factor = base_factor * impulse_bonus

    new_zone_cat = insights.loc[insights["Zone"] == new_zone, "Zone_Category"].astype(str).str.lower()
    if not new_zone_cat.empty and new_zone_cat.iloc[0] == "cold":
        predicted_factor *= 0.8

    if prod_row["Product_Name"] in premium_products and new_zone.upper() in entrance_candidates:
        predicted_factor *= 1.1
    uplift_pct = (predicted_factor - 1) * 100

    reasoning = (
        f"Moving from {current_zone} (visits {visits_current}) to {new_zone} "
        f"(visits {visits_new}) changes visibility by {footfall_ratio:.2f}x. "
        f"Conversion shifts from {conv_current:.2f} to {conv_new:.2f}. "
        f"Dwell time changes from {dwell_current:.1f}s to {dwell_new:.1f}s."
    )
    if new_zone.upper() in entrance_candidates:
        reasoning += " Entrance zone expected to boost impulse purchases."

    return {
        "product": prod_row["Product_Name"],
        "from": current_zone,
        "to": new_zone,
        "predicted_sales_uplift": f"{uplift_pct:+.0f}%",
        "reasoning": reasoning,
    }

