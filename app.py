import os
from datetime import datetime, date, timedelta, time
from typing import Dict, Any

import pandas as pd
import streamlit as st


from src.db import (
    init_db,
    get_engine,
    get_session_factory,
    Server,
    Player,
    VsDay,
    VsScoreEntry,
    get_or_create_setting,
    set_setting,
)
from src.ingest_csv import import_players_csv, import_vs_scores_csv
from src.ingest_manual import manual_add_score
from src.analytics import weekly_summaries

APP_TITLE = "Last War — VS Tracker (Online MVP)"
DB_PATH = "data/vs_tracker.sqlite3"

st.set_page_config(page_title=APP_TITLE, layout="wide")

init_db(DB_PATH)
engine = get_engine(DB_PATH)
Session = get_session_factory(engine)

st.title(APP_TITLE)

# ------------------------
# SIDEBAR
# ------------------------

with Session() as session:
    reset_str = get_or_create_setting(session, "reset_time", "00:00")

reset_time = time(int(reset_str.split(":")[0]), int(reset_str.split(":")[1]))

servers = []
with Session() as session:
    servers = session.query(Server).all()

server_name = st.sidebar.selectbox(
    "Server",
    [s.name for s in servers] if servers else [],
)

if server_name:
    server_id = [s.server_id for s in servers if s.name == server_name][0]
else:
    server_id = None

start_date = st.sidebar.date_input("From", date.today() - timedelta(days=14))
end_date = st.sidebar.date_input("To", date.today())

tabs = st.tabs(["Dashboard", "Data Import", "Admin"])

# ------------------------
# DASHBOARD
# ------------------------

with tabs[0]:
    if not server_id:
        st.warning("Create server first.")
    else:
        with Session() as session:
            q = (
                session.query(VsScoreEntry, VsDay, Player)
                .join(VsDay, VsScoreEntry.day_id == VsDay.day_id)
                .join(Player, VsScoreEntry.player_id == Player.player_id)
                .filter(VsDay.server_id == server_id)
                .filter(VsDay.date >= start_date)
                .filter(VsDay.date <= end_date)
                .all()
            )

        data = []
        for e, d, p in q:
            data.append(
                {
                    "date": d.date,
                    "player": p.current_name,
                    "points": e.points_total,
                }
            )

        df = pd.DataFrame(data)

        if df.empty:
            st.info("No data yet.")
        else:
            total = df["points"].sum()
            st.metric("Total Points", f"{total:,}")

            daily = df.groupby("date")["points"].sum().reset_index()
            daily = daily.sort_values("date")
            st.line_chart(daily, x="date", y="points")

            top = (
                df.groupby("player")["points"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )

            st.subheader("Top Players")
            st.dataframe(top, use_container_width=True)

# ------------------------
# DATA IMPORT
# ------------------------

with tabs[1]:
    st.subheader("Player Import (CSV)")
    player_file = st.file_uploader("Upload player CSV", type=["csv"])

    if player_file:
        df = pd.read_csv(player_file)
        with Session() as session:
            import_players_csv(session, df)
        st.success("Players imported.")

    st.divider()

    st.subheader("VS Points Import (CSV)")
    vs_file = st.file_uploader("Upload VS CSV", type=["csv"])

    if vs_file:
        df = pd.read_csv(vs_file)
        reset_map = {}
        for d in pd.to_datetime(df["date"]).dt.date.unique():
            reset_map[d] = datetime.combine(d, reset_time)
        with Session() as session:
            import_vs_scores_csv(session, df, reset_map)
        st.success("VS points imported.")

    st.divider()

    st.subheader("Manual Entry")
    m_date = st.date_input("Date")
    m_player = st.text_input("Player name")
    m_points = st.number_input("Points", min_value=0, value=0)

    if st.button("Add Entry"):
        with Session() as session:
            reset_ts = datetime.combine(m_date, reset_time)
            manual_add_score(session, server_id, m_date, reset_ts, m_player, m_points)
        st.success("Added.")

# ------------------------
# ADMIN
# ------------------------

with tabs[2]:
    st.subheader("Create Server")

    new_server = st.text_input("Server Name")
    if st.button("Create Server"):
        with Session() as session:
            session.add(Server(name=new_server))
            session.commit()
        st.success("Server created.")

    st.divider()

    st.subheader("Reset Time")
    new_reset = st.text_input("HH:MM", value=reset_str)
    if st.button("Save Reset"):
        with Session() as session:
            set_setting(session, "reset_time", new_reset)

        st.success("Saved.")
