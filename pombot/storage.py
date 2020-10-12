from pombot.config import Config


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

    SELECT_ALL_POMS = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID=%s;
    """

    SELECT_ALL_POMS_WITH_LIMIT = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID=%s
        ORDER BY time_set DESC
        LIMIT %s;
    """

    SELECT_ALL_POMS_CURRENT_SESSION = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID = %s
        AND current_session = 1;
    """

    SELECT_ALL_POMS_WITH_DESCRIPT = f"""
        SELECT * FROM {Config.POMS_TABLE}
        WHERE userID = %s
        AND descript = %s;
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

    DELETE_POMS = f"""
        DELETE FROM {Config.POMS_TABLE}
        WHERE userID=%s;
    """

    DELETE_POMS_WITH_ID = f"""
        DELETE FROM {Config.POMS_TABLE}
        WHERE userID=%s
        AND id=%s;
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
