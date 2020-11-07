import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime as dt
from typing import List

import mysql.connector
from discord.user import User

import pombot.errors
from pombot.config import Config, Secrets

_log = logging.getLogger(__name__)


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


@contextmanager
def _mysql_database_cursor():
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
    """The global object-relational mapping."""

    TABLES = [
        {
            "name": Config.POMS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.POMS_TABLE} (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    userID BIGINT(20),
                    descript VARCHAR(30),
                    time_set TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    current_session TINYINT(1),
                    PRIMARY KEY(id)
                );
            """
        },
        {
            "name": Config.EVENTS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.EVENTS_TABLE} (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    event_name VARCHAR(100) NOT NULL,
                    pom_goal INT(11),
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    PRIMARY KEY(id)
                );
            """
        },
    ]

    @classmethod
    def create_tables_if_not_exists(cls):
        """Create predefined DB tables if they don't already exist."""
        for table in cls.TABLES:
            table_name, table_create_query = table.values()
            _log.info('Creating "%s" table, if it does not exist', table_name)

            with _mysql_database_cursor() as cursor:
                cursor.execute(table_create_query)

    @classmethod
    def delete_all_rows_from_all_tables(cls):
        """Delete all rows from all tables.

        This is a dangerous function and should only be run by developers on
        development machines.
        """
        _log.info("Deleting tables... ")

        with _mysql_database_cursor() as cursor:
            for table_name in (table["name"] for table in cls.TABLES):
                cursor.execute(f"DELETE FROM {table_name};")

        _log.info("Tables deleted.")

    @staticmethod
    def get_num_poms_for_all_users() -> int:
        """Return the number of poms in the database as an int."""
        query = f"SELECT * FROM {Config.POMS_TABLE};"

        with _mysql_database_cursor() as cursor:
            cursor.execute(query)
            num_rows = cursor.rowcount

        return num_rows

    @staticmethod
    def get_all_poms_for_user(user: User) -> List[Pom]:
        """Return all submitted poms from user as a list."""
        query = f"""
            SELECT * FROM {Config.POMS_TABLE}
            WHERE userID=%s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))
            rows = cursor.fetchall()

        return [Pom(*row) for row in rows]

    @staticmethod
    def add_poms_to_user_session(user: User, descript: str, count: int):
        """Add a number of user poms."""
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

        with _mysql_database_cursor() as cursor:
            cursor.executemany(query, poms)

    @staticmethod
    def clear_user_session_poms(user: User):
        """Set all active session poms to be non-active."""
        query = f"""
            UPDATE  {Config.POMS_TABLE}
            SET current_session = 0
            WHERE userID = %s
            AND current_session = 1;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))

    @staticmethod
    def delete_all_user_poms(user: User):
        """Remove all poms for user."""
        query = f"""
            DELETE FROM {Config.POMS_TABLE}
            WHERE userID=%s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, ))

    @staticmethod
    def delete_most_recent_user_poms(user: User, count: int):
        """Delete `count` most recent poms for `user`."""
        query = f"""
            DELETE FROM {Config.POMS_TABLE}
            WHERE userID=%s
            ORDER BY time_set DESC
            LIMIT %s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (user.id, count))

    @staticmethod
    def get_ongoing_events() -> List[Event]:
        """Return a list of ongoing Events."""
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE start_date <= %s
            AND end_date >= %s;
        """

        current_date = dt.now()

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (current_date, current_date))
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    def get_num_poms_for_date_range(start: dt, end: dt) -> int:
        """Return the number of poms set within a date range."""
        query = f"""
            SELECT * FROM {Config.POMS_TABLE}
            WHERE time_set >= %s
            AND time_set <= %s;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (start, end))
            rows = cursor.fetchall()

        return len(rows)

    @staticmethod
    def add_new_event(name: str, goal: int, start: dt, end: dt):
        """Add a new event row."""
        query = f"""
            INSERT INTO {Config.EVENTS_TABLE} (
                event_name,
                pom_goal,
                start_date,
                end_date
            )
            VALUES (%s, %s, %s, %s);
        """

        with _mysql_database_cursor() as cursor:
            try:
                cursor.execute(query, (name, goal, start, end))
            except mysql.connector.DatabaseError as exc:
                # Give a nicer error message than the mysql default.
                raise pombot.errors.EventCreationError(exc.msg)

    @staticmethod
    def get_all_events() -> List[Event]:
        """Return a list of all events."""
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            ORDER BY start_date;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    def get_overlapping_events(start: dt, end: dt) -> List[Event]:
        """Return a list of events in the database which overlap with the
        dates specified.
        """
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE %s < end_date
            AND %s > start_date;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (start, end))
            rows = cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    def delete_event(name: str):
        """Delete the named event from the DB."""
        query = f"""
            DELETE FROM {Config.EVENTS_TABLE}
            WHERE event_name=%s
            ORDER BY start_date
            LIMIT 1;
        """

        with _mysql_database_cursor() as cursor:
            cursor.execute(query, (name, ))
