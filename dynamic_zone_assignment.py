import pandas as pd
import os
import json
from datetime import datetime

from conversion_rate_analysis import calculate_zone_conversion_rates
from revenue_per_sqft_calculator import calculate_revenue_per_sqft
from relocation_intelligence import generate_relocation_scores

INSIGHTS_DIR = "insights"
DATA_DIR = "data"
DECISION_LOG_PATH = os.path.join("agent_memory", "decision_log.json")
FINAL_INSIGHTS_PATH = os.path.join(INSIGHTS_DIR, "final_product_insights.csv")
RELOCATION_PLAN_PATH = os.path.join(INSIGHTS_DIR, "relocation_plan.csv")
ZONE_PERF_PATH = os.path.join(INSIGHTS_DIR, "zone_performance.csv")


def _load_decision_log():
    if not os.path.exists(DECISION_LOG_PATH):
        return []
    try:
        with open(DECISION_LOG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    min_v = series.min()
    max_v = series.max()
    if max_v - min_v == 0:
        return pd.Series(0, index=series.index)
    return (series - min_v) / (max_v - min_v)


def _build_zone_performance(final_df: pd.DataFrame) -> pd.DataFrame:
    visits = final_df.groupby("Zone")["Visits"].sum().rename("footfall")
    conv_df = calculate_zone_conversion_rates()
    rev_df = calculate_revenue_per_sqft()

    zone_df = pd.DataFrame({"zone_id": visits.index, "footfall": visits.values})
    if not conv_df.empty:
        zone_df = zone_df.merge(
            conv_df[["Zone", "Conversion_Rate"]],
            left_on="zone_id",
            right_on="Zone",
            how="left",
        ).drop(columns=["Zone"])
    if not rev_df.empty:
        zone_df = zone_df.merge(
            rev_df[["Zone", "Revenue_per_sqft"]],
            left_on="zone_id",
            right_on="Zone",
            how="left",
        ).drop(columns=["Zone"])
    zone_df.fillna(0, inplace=True)

    zone_df["hot_score"] = (
        _normalize(zone_df["footfall"]) * 0.5
        + _normalize(zone_df.get("Conversion_Rate", pd.Series(0, index=zone_df.index))) * 0.3
        + _normalize(zone_df.get("Revenue_per_sqft", pd.Series(0, index=zone_df.index))) * 0.2
    )

    zone_df.sort_values("hot_score", ascending=False, inplace=True)
    zone_df.to_csv(ZONE_PERF_PATH, index=False)
    return zone_df


def assign_recommended_zones(top_n: int | None = None) -> pd.DataFrame:
    if not os.path.exists(FINAL_INSIGHTS_PATH):
        print("final_product_insights.csv not found")
        return pd.DataFrame()

    final_df = pd.read_csv(FINAL_INSIGHTS_PATH)
    if final_df.empty:
        print("final_product_insights.csv is empty")
        return pd.DataFrame()

    ri_df = generate_relocation_scores()
    if ri_df.empty:
        print("relocation scores not available")
        return pd.DataFrame()

    zone_perf = _build_zone_performance(final_df)
    hot_zones = zone_perf["zone_id"].tolist()
    if not hot_zones:
        print("no zones available")
        return pd.DataFrame()

    ri_df = ri_df.sort_values("Relocation_Score", ascending=False)
    if top_n:
        ri_df = ri_df.head(top_n)

    recent_moves = {entry.get("product_name") for entry in _load_decision_log()}
    zone_capacity = final_df["Zone"].value_counts().to_dict()
    max_capacity = {z: zone_capacity.get(z, 0) + 5 for z in hot_zones}
    assigned_counts = {z: 0 for z in hot_zones}

    plan = []
    for _, row in ri_df.iterrows():
        if row["Product_Name"] in recent_moves:
            continue
        current_zone = row["Current_Zone"]
        for zone in hot_zones:
            if zone == current_zone:
                continue
            if assigned_counts[zone] >= max_capacity[zone]:
                continue
            final_df.loc[final_df["Product_ID"] == row["Product_ID"], "Recommended_Zone"] = zone
            assigned_counts[zone] += 1
            plan.append(
                {
                    "product_id": row["Product_ID"],
                    "current_zone": current_zone,
                    "recommended_zone": zone,
                    "relocation_score": row["Relocation_Score"],
                    "reason": row.get("Why_This_Zone", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            break

    final_df.to_csv(FINAL_INSIGHTS_PATH, index=False)
    pd.DataFrame(plan).to_csv(RELOCATION_PLAN_PATH, index=False)
    return final_df


if __name__ == "__main__":
    assign_recommended_zones()
