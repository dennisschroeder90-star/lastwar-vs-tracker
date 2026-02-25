import pandas as pd
from datetime import timedelta


def weekly_summaries(df, end_date):
    start = end_date - timedelta(days=6)
    week = df[(df["date"] >= start) & (df["date"] <= end_date)]

    summary = (
        week.groupby("player")["points"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    return summary