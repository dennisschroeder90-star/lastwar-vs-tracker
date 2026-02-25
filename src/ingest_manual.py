from .db import VsDay, VsScoreEntry, Player


def manual_add_score(session, server_id, d, reset_ts, player_name, points):
    day = session.query(VsDay).filter_by(server_id=server_id, date=d).first()
    if not day:
        day = VsDay(server_id=server_id, date=d, reset_ts=reset_ts)
        session.add(day)
        session.commit()

    player = session.query(Player).filter_by(
        server_id=server_id,
        current_name=player_name,
    ).first()

    if not player:
        return

    entry = VsScoreEntry(
        day_id=day.day_id,
        player_id=player.player_id,
        points_total=points,
        source="manual",
    )
    session.add(entry)
    session.commit()