from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import List

import mysql.connector
from discord.user import User

from pombot.config import Config, Secrets


@dataclass
class Pom:
    """A pom, as described in order from the database."""
    pom_id: int
    user_id: int
    descript: str
    time_set: datetime
    session: int

    def is_current_session(self) -> bool:
        """Return whether this pom is in the user's current session."""
        return bool(self.session)


class PomSql:
    """SQL queries for poms."""

    CREATE_TABLE = f"""
        CREATE TABLE IF NOT EXISTS {Config.POMS_TABLE} (
            id INT(11) NOT NULL AUTO_INCREMENT,
            userID BIGINT(20),
            descript VARCHAR(30),
            time_set TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            current_session TINYINT(1),
            PRIMARY KEY(id)
        );
    """

    INSERT_QUERY = f"""
        INSERT INTO {Config.POMS_TABLE} (
            userID,
            descript,
            time_set,
            current_session
        )
        VALUES (%s, %s, %s, %s);
    """

    SELECT_ALL_POMS_BY_USERID = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID=%s;
    """

    SELECT_ALL_POMS_CURRENT_SESSION = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID = %s
        AND current_session = 1;
    """

    EVENT_SELECT = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE time_set >= %s
        AND time_set <= %s;
    """

    UPDATE_REMOVE_ALL_POMS_FROM_SESSION = f"""
        UPDATE  {Config.POMS_TABLE}
        SET current_session = 0
        WHERE userID = %s
        AND current_session = 1;
    """

    DELETE_ALL_POMS_FOR_USER = f"""
        DELETE FROM {Config.POMS_TABLE}
        WHERE userID=%s;
    """

    DELETE_RECENT_POMS_FOR_USER = f"""
        DELETE FROM {Config.POMS_TABLE}
        WHERE userID=%s
        ORDER BY time_set DESC
        LIMIT %s;
    """


class EventSql:
    """SQL queries for events."""

    CREATE_TABLE = f"""
        CREATE TABLE IF NOT EXISTS {Config.EVENTS_TABLE} (
            id INT(11) NOT NULL AUTO_INCREMENT,
            event_name VARCHAR(100) NOT NULL,
            pom_goal INT(11),
            start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP NOT NULL DEFAULT 0,
            PRIMARY KEY(id)
        );
    """

    EVENT_ADD = f"""
        INSERT INTO {Config.EVENTS_TABLE} (
            event_name,
            pom_goal,
            start_date,
            end_date
        )
        VALUES (%s, %s, %s, %s);
    """

    SELECT_EVENT = f"""
        SELECT * FROM {Config.EVENTS_TABLE}
        WHERE start_date <= %s
        AND end_date >= %s;
    """

@contextmanager
def mysql_database_cursor():
    db_config = {
        "host": Secrets.MYSQL_HOST,
        "user": Secrets.MYSQL_USER,
        "password": Secrets.MYSQL_PASSWORD,
        "database": Secrets.MYSQL_DATABASE,
    }

    if Config.USE_CONNECTION_POOL:
        db_config.update({"pool_size": Config.CONNECTION_POOL_SIZE})

    db_connection = mysql.connector.connect(**db_config)
    cursor = db_connection.cursor(buffered=True)

    yield cursor

    db_connection.commit()
    cursor.close()
    db_connection.close()


class Storage:
    @classmethod
    def get_all_poms_for_user(cls, user: User) -> List[Pom]:
        with mysql_database_cursor() as cursor:
            cursor.execute(PomSql.SELECT_ALL_POMS_BY_USERID, (user.id, ))
            rows = cursor.fetchall()

        return [Pom(*row) for row in rows]

    @classmethod
    def add_poms_to_user_session(cls, user: User, descript: str, count: int):
        descript = descript or None
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        poms = [(user.id, descript, now, True) for _ in range(count)]

        with mysql_database_cursor() as cursor:
            cursor.executemany(PomSql.INSERT_QUERY, poms)

    @classmethod
    def clear_user_session_poms(cls, user: User):
        with mysql_database_cursor() as cursor:
            cursor.execute(PomSql.UPDATE_REMOVE_ALL_POMS_FROM_SESSION, (user.id, ))

    @classmethod
    def delete_all_user_poms(cls, user: User):
        with mysql_database_cursor() as cursor:
            cursor.execute(PomSql.DELETE_ALL_POMS_FOR_USER, (user.id, ))

    @classmethod
    def delete_most_recent_user_poms(cls, user: User, count: int):
        with mysql_database_cursor() as cursor:
            cursor.execute(PomSql.DELETE_RECENT_POMS_FOR_USER, (user.id, count))
