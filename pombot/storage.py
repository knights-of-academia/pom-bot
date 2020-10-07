import textwrap

from pombot.config import Config


class PomSql:
    INSERT_QUERY = textwrap.dedent(f"""\
        INSERT INTO {Config.POMS_TABLE} (
            userID,
            descript,
            time_set,
            current_session
        )
        VALUES (%s, %s, %s, %s);
    """)

    SELECT_ALL_POMS = textwrap.dedent(f"""\
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID=%s;
    """)

    SELECT_ALL_POMS_CURRENT_SESSION = textwrap.dedent(f"""\
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID = %s
        AND current_session = 1;
    """)

    EVENT_SELECT = textwrap.dedent(f"""\
        SELECT * FROM {Config.POMS_TABLE}
        WHERE time_set >= %s
        AND time_set <= %s;
    """)

    UPDATE_SESSION = textwrap.dedent(f"""\
        UPDATE  {Config.POMS_TABLE}
        SET current_session = 0
        WHERE userID = %s
        AND current_session = 1;
    """)

    DELETE_POMS = textwrap.dedent(f"""\
        DELETE FROM {Config.POMS_TABLE}
        WHERE userID=%s;
    """)


class EventSql:
    EVENT_ADD = textwrap.dedent(f"""\
        INSERT INTO {Config.EVENTS_TABLE} (
            event_name,
            pom_goal,
            start_date,
            end_date
        )
        VALUES (%s, %s, %s, %s);
    """)

    SELECT_EVENT = textwrap.dedent(f"""\
        SELECT * FROM {Config.EVENTS_TABLE}
        WHERE start_date <= %s
        AND end_date >= %s;
    """)
