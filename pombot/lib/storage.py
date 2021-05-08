import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime as dt
from datetime import time, timezone
from typing import Iterable, List, Optional, Set, Union

import aiomysql
from discord.user import User as DiscordUser

import pombot.lib.errors as errors
import pombot.lib.pom_wars.errors as war_crimes
from pombot.config import Config, Secrets
from pombot.lib.types import Action, ActionType, DateRange, Event, Pom, SessionType
from pombot.lib.types import User as PombotUser
from pombot.state import State

_log = logging.getLogger(__name__)


@asynccontextmanager
async def _mysql_database_connection():
    db_config = {
        "db":       Secrets.MYSQL_DATABASE,
        "host":     Secrets.MYSQL_HOST,
        "user":     Secrets.MYSQL_USER,
        "password": Secrets.MYSQL_PASSWORD,
        "loop":     State.event_loop,
        "charset":  "utf8",
    }
    connection: aiomysql.Connection = await aiomysql.connect(**db_config)

    try:
        yield connection
    except aiomysql.Error:
        await connection.rollback()

        # Handle error at callsite.
        raise
    else:
        await connection.commit()
    finally:
        # aiomysql.Connection.close() returns None, not a coro.
        connection.close()


@asynccontextmanager
async def _mysql_database_cursor():
    async with _mysql_database_connection() as connection:
        cursor: aiomysql.Cursor =  await connection.cursor()

        try:
            yield cursor
        finally:
            await cursor.close()


def _replace_further_occurances(text: str, old: str, new: str) -> str:
    try:
        offset = text.index(old) + 1
    except ValueError:
        return text

    return text[:offset] + text[offset:].replace(old, new)


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
        {
            "name": Config.USERS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.USERS_TABLE} (
                    userID BIGINT(20) NOT NULL UNIQUE,
                    timezone VARCHAR(8) NOT NULL,
                    team VARCHAR(10) NOT NULL,
                    inventory_string TEXT(30000),
                    player_level TINYINT(1) NOT NULL DEFAULT 1,
                    attack_level TINYINT(1) NOT NULL DEFAULT 1,
                    heavy_attack_level TINYINT(1) NOT NULL DEFAULT 1,
                    defend_level TINYINT(1) NOT NULL DEFAULT 1,
                    PRIMARY KEY(userID)
                );
            """
        },
        {
            "name": Config.ACTIONS_TABLE,
            "create_query": f"""
                CREATE TABLE IF NOT EXISTS {Config.ACTIONS_TABLE} (
                    id INT(11) NOT NULL AUTO_INCREMENT,
                    userID BIGINT(20),
                    team VARCHAR(10) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    was_successful TINYINT(1) NOT NULL,
                    was_critical TINYINT(1),
                    items_dropped VARCHAR(30),
                    damage INT(4),
                    time_set TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(id)
                );
            """
        },
    ]

    @classmethod
    async def create_tables_if_not_exists(cls):
        """Create predefined DB tables if they don't already exist."""
        # Tables are read first instead of purely relying on the "IF NOT
        # EXISTS" SQL syntax to avoid an unnecessary warning from aiomysql.
        async with _mysql_database_cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            existing_tables = await cursor.fetchall()

        existing_table_names = set(row[0] for row in existing_tables)
        required_table_names = set(table["name"] for table in cls.TABLES)
        names_of_tables_to_create = required_table_names - existing_table_names

        for table_to_create in names_of_tables_to_create:
            _log.info('Creating table: %s', table_to_create)
            create_query = next(table["create_query"] for table in cls.TABLES
                                if table["name"] == table_to_create)

            async with _mysql_database_cursor() as cursor:
                await cursor.execute(create_query)

    @classmethod
    async def delete_all_rows_from_all_tables(cls):
        """Delete all rows from all tables.

        This is a dangerous function and should only be run by developers on
        development machines.
        """
        _log.info("Deleting tables... ")
        async with _mysql_database_cursor() as cursor:
            for table_name in (table["name"] for table in cls.TABLES):
                await cursor.execute(f"DELETE FROM {table_name};")
        _log.info("Tables deleted.")

    @staticmethod
    async def add_poms_to_user_session(
        user: DiscordUser,
        descript: Optional[Union[str, Iterable]],
        count: int,
        time_set: dt = None,
    ):
        """Add a number of user poms.

        If `descript` is specified as a non-string iterable, like a list or
        generator, then this will check that we're in a unit test and fail if
        not. This is because it is generally only possible to have one pom
        description per user command specified, but this makes unit tests that
        require many poms in the DB very slow.
        """
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
        time_set = time_set or dt.now()

        if type(descript) in [str, type(None)]:
            poms = [(user.id, descript, time_set, True) for _ in range(count)]
        else:
            assert "unittest" in sys.modules, \
                f"{type(descript)} not allowed for descript outside of unit tests"

            poms = [(user.id, desc, time_set, True)
                    for desc in descript
                    for _ in range(count)]

        async with _mysql_database_cursor() as cursor:
            await cursor.executemany(query, poms)

    @staticmethod
    async def bank_user_session_poms(user: DiscordUser) -> int:
        """Set all active session poms to be non-active and return number of
        rows affected.
        """
        query = f"""
            UPDATE  {Config.POMS_TABLE}
            SET current_session = 0
            WHERE userID = %s
            AND current_session = 1;
        """

        async with _mysql_database_cursor() as cursor:
            rows_affected = await cursor.execute(query, (user.id, ))

        return rows_affected

    @staticmethod
    async def delete_poms(
        *,
        user: DiscordUser,
        time_set: dt = None,
        session: SessionType = None,
     ) -> int:
        """Delete a user's poms matching the criteria.

        NOTE: When only the user is specified, all of their poms will be
        deleted!

        @param user Only match poms for this user.
        @param time_set Only match poms with this timestamp value.
        @param session Only remove poms from this session.
        @return Number of rows deleted.
        """
        query = [f"DELETE FROM {Config.POMS_TABLE} WHERE userID=%s"]
        args = [user.id]

        if time_set:
            query += ["WHERE time_set=%s"]
            args += [time_set]

        if session:
            if (not isinstance(session, SessionType) or
                    session not in [SessionType.CURRENT, SessionType.BANKED]):
                raise RuntimeError("Invalid session type for removal.")

            query += ["WHERE current_session=%s"]
            args += [int(session == SessionType.CURRENT)]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "AND")

        async with _mysql_database_cursor() as cursor:
            num_rows_removed = await cursor.execute(query_str, args)

        return num_rows_removed

    @staticmethod
    async def get_ongoing_events() -> List[Event]:
        """Return a list of ongoing Events."""
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE start_date <= %s
            AND end_date >= %s;
        """

        current_date = dt.now()

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (current_date, current_date))
            rows = await cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    async def get_poms(
        *,
        user: DiscordUser = None,
        descript = None,
        date_range: DateRange = None,
        limit: int = None
    ) -> List[Pom]:
        """Get a list of poms from storage matching certain criteria. When
        limit is set, then the order is assumed to be most recent first.

        @param user Only match poms for this user.
        @param date_range Only match poms within this date range.
        @param limit Maximum length of the returned list.
        @return List of Pom objects.
        """
        query = [f"SELECT * FROM {Config.POMS_TABLE}"]
        args = []

        if user:
            query += ["WHERE userID=%s"]
            args += [user.id]

        if descript:
            query += ["WHERE descript=%s"]
            args += [descript]

        if date_range:
            query += ["WHERE time_set >= %s AND time_set <= %s"]
            args += [date_range.start_date, date_range.end_date]

        if limit:
            query += ["ORDER BY time_set DESC LIMIT %s"]
            args += [limit]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "AND")

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query_str, args)
            rows = await cursor.fetchall()

        return [Pom(*row) for row in rows]

    @staticmethod
    async def add_new_event(name: str, goal: int, date_range: DateRange):
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
        args = name, goal, date_range.start_date, date_range.end_date

        async with _mysql_database_cursor() as cursor:
            try:
                await cursor.execute(query, args)
            except aiomysql.DataError as exc:
                # Give a nicer error message than the mysql default. This has
                # been tested to handle "event name too long" and "pom_goal"
                # out of range.
                raise errors.EventCreationError(exc.args[-1]) from exc

    @staticmethod
    async def get_all_events() -> List[Event]:
        """Return a list of all events."""
        # Tech debt: merge this function into `get_events`.
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            ORDER BY start_date;
        """

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    async def get_overlapping_events(date_range: DateRange) -> List[Event]:
        """Return a list of events in the database which overlap with the
        dates specified.
        """
        # Tech debt: merge this function into `get_events`.
        query = f"""
            SELECT * FROM {Config.EVENTS_TABLE}
            WHERE %s < end_date
            AND %s > start_date;
        """

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (date_range.start_date, date_range.end_date))
            rows = await cursor.fetchall()

        return [Event(*row) for row in rows]

    @staticmethod
    async def delete_event(name: str):
        """Delete the named event from the DB."""
        query = f"""
            DELETE FROM {Config.EVENTS_TABLE}
            WHERE event_name=%s
            ORDER BY start_date
            LIMIT 1;
        """

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (name, ))

    @classmethod
    async def add_user(cls, user_id: str, zone: timezone, team: str):
        """Add a user into the users table."""
        query = f"""
            INSERT INTO {Config.USERS_TABLE} (
                userID,
                timezone,
                team
            )
            VALUES (%s, %s, %s);
        """

        zone_str = time(tzinfo=zone).strftime('%z')

        async with _mysql_database_cursor() as cursor:
            try:
                await cursor.execute(query, (user_id, zone_str, team))
            except aiomysql.IntegrityError as exc:
                user = await cls.get_user_by_id(user_id)
                raise war_crimes.UserAlreadyExistsError(user.team) from exc

    @staticmethod
    async def set_user_timezone(user_id: str, zone: timezone):
        """Set the user timezone."""
        query = f"""
            UPDATE {Config.USERS_TABLE}
            SET timezone=%s
            WHERE userID=%s
        """

        zone_str = time(tzinfo=zone).strftime('%z')

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (zone_str, user_id))

    @staticmethod
    async def update_user_team(user_id: str, team: str):
        """Set the user team."""
        query = f"""
            UPDATE {Config.USERS_TABLE}
            SET team=%s
            WHERE userID=%s
        """

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (team, user_id))

    @staticmethod
    async def update_user_poms_descriptions(
        user: DiscordUser,
        old_description: str,
        new_description: str,
        banked_poms_only: bool = False,
        session_poms_only: bool = False,
    ) -> int:
        """Update user poms matching a description to a new description."""
        if banked_poms_only and session_poms_only:
            raise RuntimeError("Only one of banked_poms_only or session_poms_only allowed.")

        query = f"""
            UPDATE {Config.POMS_TABLE}
            SET descript=%s
            WHERE userID=%s
            AND descript=%s
        """

        if banked_poms_only:
            query += "AND current_session=0"

        if session_poms_only:
            query += "AND current_session=1"

        async with _mysql_database_cursor() as cursor:
            rows_affected = await cursor.execute(query, (new_description, user.id, old_description))

        return rows_affected

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[PombotUser]:
        """Return a single user by its userID."""
        query = f"""
            SELECT * FROM {Config.USERS_TABLE}
            WHERE userID=%s;
        """

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (user_id,))
            row = await cursor.fetchone()

        if not row:
            raise war_crimes.UserDoesNotExistError()

        return PombotUser(*row)

    @staticmethod
    async def get_users_by_id(user_ids: List[int]) -> Set[PombotUser]:
        """Return a list of users from a list of userID's.

        This is a small optimization function to call the storage a single
        time to return multiple unique users, instead of calling it one time
        for each user.
        """
        if not user_ids:
            return []

        query = [f"SELECT * FROM {Config.USERS_TABLE}"]
        values = []

        for user_id in user_ids:
            query += ["WHERE userID=%s"]
            values += [user_id]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "OR")

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query_str, values)
            rows = await cursor.fetchall()

        return {PombotUser(*r) for r in rows}

    @staticmethod
    async def add_pom_war_action(
        user: DiscordUser,
        team: str,
        action_type: ActionType,
        was_successful: bool,
        was_critical: bool,
        items_dropped: str,
        damage: int,
        time_set: dt,
    ):
        """Add an action to the ledger."""
        query = f"""
            INSERT INTO {Config.ACTIONS_TABLE} (
                userID,
                team,
                type,
                was_successful,
                was_critical,
                items_dropped,
                damage,
                time_set
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (user.id, team, action_type.value, was_successful,
                  was_critical, items_dropped, (damage or 0) * 100, time_set)

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, values)

    @staticmethod
    async def get_actions(
        *,
        action_type: ActionType = None,
        user: DiscordUser = None,
        team: str = None,
        was_successful = None,
        date_range: DateRange = None,
    ) -> List[Action]:
        """Get a list of actions from storage matching certain criteria.

        This function has the potential to return a large list of actions, so
        it is recommended to provide a date_range.

        @param user Only match actions for this user.
        @param date_range Only match actions within this date range.
        @return List of Action objects.
        """
        query = [f"SELECT * FROM {Config.ACTIONS_TABLE}"]
        values = []

        if action_type:
            query += [f"WHERE type=%s"]
            values += [action_type.value]

        if user:
            query += [f"WHERE userID=%s"]
            values += [user.id]

        if team:
            query += [f"WHERE team=%s"]
            values += [team]

        if was_successful:
            query += [f"WHERE was_successful=%s"]
            values += [1]

        if date_range:
            query += ["WHERE time_set >= %s", "AND time_set <= %s"]
            values += [date_range.start_date, date_range.end_date]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "AND")

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query_str, values)
            rows = await cursor.fetchall()

        return [Action(*row) for row in rows]

    @staticmethod
    async def count_rows_in_table(
        table: str,
        *,
        action_type: ActionType = None,
        team: str = None,
    ) -> int:
        """Get number of users on a team.

        The team parameter is a string here to avoid a circular reference.

        @param table The table from which to count.
        @param action_type Consider only these types of actions.
        @param team Team name as a string.
        @return Count of users on this team.
        """
        query = [f"SELECT COUNT(1) FROM {table}"]
        values = []

        if action_type:
            query += [f"WHERE type=%s"]
            values += [action_type.value]

        if team:
            query += [f"WHERE team=%s"]
            values += [team]

        query_str = _replace_further_occurances(" ".join(query), "WHERE", "AND")

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query_str, values)
            row, = await cursor.fetchone()

        return int(row)

    @staticmethod
    async def sum_team_damage(team: str) -> int:
        """Get sum of the damage column for a team.

        The team parameter is a string here to avoid a circular reference.

        @param team Team name as a string.
        @return Sum of the damage that the team has done thus far.
        """
        query = f"""
            SELECT SUM(damage) FROM {Config.ACTIONS_TABLE}
            WHERE team=%s;
        """

        async with _mysql_database_cursor() as cursor:
            await cursor.execute(query, (team,))
            row, = await cursor.fetchone()

        return int(row or 0)
