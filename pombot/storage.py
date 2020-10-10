from pombot.config import Config


class PomSql:
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

    UPDATE_SESSION = f"""
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