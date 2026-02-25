import pandas as pd
from datetime import datetime
from .db import Server, Player, VsDay, VsScoreEntry


def import_players_csv(session, df):
    for _, row in df.iterrows():
        server = session.query(Server).filter_by(name=row["server_name"]).first()
        if not server:
            server = Server(name=row["server_name"])
            session.add(server)
            session.commit()

        player = Player(
            server_id=server.server_id,
            current_name=row["player_name"],
        )
        session.add(player)
    session.commit()


def import_vs_scores_csv(session, df, reset_map):
    for _, row in df.iterrows():
        server = session.query(Server).filter_by(name=row["server_name"]).first()
        if not server:
            continue

        d = datetime.strptime(row["date"], "%Y-%m-%d").date()
        day = session.query(VsDay).filter_by(server_id=server.server_id, date=d).first()
        if not day:
            day = VsDay(server_id=server.server_id, date=d, reset_ts=reset_map[d])
            session.add(day)
            session.commit()

        player = session.query(Player).filter_by(
            server_id=server.server_id,
            current_name=row["player_name"],
        ).first()

        if not player:
            continue

        entry = VsScoreEntry(
            day_id=day.day_id,
            player_id=player.player_id,
            points_total=row["points_total"],
            source="csv",
        )
        session.add(entry)

    session.commit()