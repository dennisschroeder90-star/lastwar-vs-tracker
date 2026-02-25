from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Server(Base):
    __tablename__ = "server"
    server_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)


class Player(Base):
    __tablename__ = "player"
    player_id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("server.server_id"))
    current_name = Column(String)


class VsDay(Base):
    __tablename__ = "vs_day"
    day_id = Column(Integer, primary_key=True)
    server_id = Column(Integer)
    date = Column(Date)
    reset_ts = Column(DateTime)


class VsScoreEntry(Base):
    __tablename__ = "vs_score_entry"
    entry_id = Column(Integer, primary_key=True)
    day_id = Column(Integer)
    player_id = Column(Integer)
    points_total = Column(Integer)
    source = Column(String)
    confidence = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "setting"
    key = Column(String, primary_key=True)
    value = Column(String)


def get_engine(path):
    return create_engine(f"sqlite:///{path}")


def get_session_factory(engine):
    return sessionmaker(bind=engine)


def init_db(path):
    engine = get_engine(path)
    Base.metadata.create_all(engine)


def get_or_create_setting(session, key, default):
    s = session.get(Setting, key)
    if not s:
        s = Setting(key=key, value=default)
        session.add(s)
        session.commit()
    return s.value


def set_setting(session, key, value):
    s = session.get(Setting, key)
    if not s:
        s = Setting(key=key, value=value)
        session.add(s)
    else:
        s.value = value
    session.commit()