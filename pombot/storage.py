from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime as dt
from typing import List

import mysql.connector
from discord.user import User

import pombot.errors
from pombot.config import Config, Secrets


@dataclass
class Pom:
    """A pom, as described, in order, from the database."""
    pom_id: int
    user_id: int
    descript: str
    time_set: dt
    session: int

    def is_current_session(self) -> bool:
        """Return whether this pom is in the user's current session."""
        return bool(self.session)


@dataclass
class Event:
    """An event, as described, in order, from the database."""
    event_id: int
    event_name: str
    pom_goal: int
    start_date: dt
    end_date: dt


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

    try:
        yield cursor
    finally:
        db_connection.commit()
        cursor.close()
        db_connection.close()


class Storage:
    @classmethod
    def get_num_poms_for_all_users(cls) -> int:
        query = f"SELECT * FROM {Config.POMS_TABLE};"

        with mysql_database_cursor() as cursor:
            cursor.execute(query)
            num_rows = cursor.rowcount

        return num_rows

    @classmethod
    def get_all_poms_for_user(cls, user: User) -> List[Pom]:
        query = f"""
            SELECT * FROM {Config.POMS_TABLE}
            WHERE userID=%s;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))
            rows = cursor.fetchall()

        return [Pom(*row) for row in rows]

    @classmethod
    def add_poms_to_user_session(cls, user: User, descript: str, count: int):
        query = f"""
            INSERT INTO {Config.POMS_TABLE} (
                userID,
                descript,
                time_set,
                current_session
            )
            VALUES (%s, %s, %s, %s);
        """

        descript = descript or None
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        poms = [(user.id, descript, now, True) for _ in range(count)]

        with mysql_database_cursor() as cursor:
            cursor.executemany(query, poms)

    @classmethod
    def clear_user_session_poms(cls, user: User):
        query = f"""
            UPDATE  {Config.POMS_TABLE}
            SET current_session = 0
            WHERE userID = %s
            AND current_session = 1;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))

    @classmethod
    def delete_all_user_poms(cls, user: User):
        query = f"""
            DELETE FROM {Config.POMS_TABLE}
            WHERE userID=%s;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))

    @classmethod
    def delete_most_recent_user_poms(cls, user: User, count: int):
        query = f"""
            DELETE FROM {Config.POMS_TABLE}
            WHERE userID=%s
            ORDER BY time_set DESC
            LIMIT %s;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, count))

    @classmethod
    def get_ongoing_events(cls) -> List[Event]:
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE start_date <= %s
            AND end_date >= %s;
        """

        current_date = dt.now()

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (current_date, current_date))
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @classmethod
    def get_num_poms_for_date_range(cls, start: dt, end: dt) -> int:
        query = f"""
            SELECT * FROM {Config.POMS_TABLE}
            WHERE time_set >= %s
            AND time_set <= %s;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (start, end))
            rows = cursor.fetchall()

        return len(rows)

    @classmethod
    def add_new_event(cls, name: str, goal: int, start: dt, end: dt):
        query = f"""
            INSERT INTO {Config.EVENTS_TABLE} (
                event_name,
                pom_goal,
                start_date,
                end_date
            )
            VALUES (%s, %s, %s, %s);
        """

        with mysql_database_cursor() as cursor:
            try:
                cursor.execute(query, (name, goal, start, end))
            except mysql.connector.DatabaseError as exc:
                # Give a nicer error message than the mysql default.
                raise pombot.errors.EventCreationError(exc.msg)

    @classmethod
    def get_all_events(cls) -> List[Event]:
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            ORDER BY start_date;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @classmethod
    def get_overlapping_events(cls, start: dt, end: dt) -> List[Event]:
        """Return a list of events in the database which overlap with the
        dates specified.
        """
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE %s < end_date
            AND %s > start_date;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (start, end))
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @classmethod
    def delete_event(cls, name: str):
        query = f"""
            DELETE FROM {Config.EVENTS_TABLE}
            WHERE event_name=%s
            ORDER BY start_date
            LIMIT 1;
        """

        with mysql_database_cursor() as cursor:
            cursor.execute(query, (name, ))
