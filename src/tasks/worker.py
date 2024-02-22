from src.services import profiles_services, migration_services, mission_services
from src.log_config import _logger
from src import db


def delete_missions_schedule(mission_id, teams_id):
    _logger.debug("Start delete the mission")
    migration_services.set_search_path(teams_id)
    mission_services.delete_mission(mission_id)
    db.session.commit()
    _logger.debug("Delete mission ok")


def create_profiles(profiles, user_id, device_id, teams_id):
    migration_services.set_search_path(teams_id)
    success_number = 0
    error_number = 0
    for data in profiles:
        try:
            data["owner"] = user_id  # set owner
            data["user_access"] = user_id
            profile = profiles_services.create_profile(data, device_id, user_id)
            if profile:
                success_number += 1
                db.session.flush()
        except Exception as ex:
            _logger.exception(ex)
            error_number += 1
    db.session.commit()
    return True


def delete_profile(profile_id, user_id, device_id, teams_id):
    migration_services.set_search_path(teams_id)
    profiles_services.delete_profile(profile_id, user_id, device_id)
    db.session.commit()


def update_profile(profile_id, teams_id, data):
    migration_services.set_search_path(teams_id)
    profiles_services.update_profile(profile_id, data)
    db.session.commit()


def update_click_count(teams_id):
    # Define the raw SQL query
    migration_services.set_search_path(teams_id)
    sql_query = (
        f"\n"
        f"    WITH Clicks AS (\n"
        f"        SELECT\n"
        f"            g.group_id,\n"
        f"            COUNT(e.profile_id_interact) AS total_clicks_giver\n"
        f"        FROM\n"
        f'            "public".user u \n'
        f"            JOIN profiles p ON u.user_id = p.owner\n"
        f"            JOIN user_group ug ON ug.user_id = u.user_id \n"
        f'            JOIN "groups" g ON g.group_id = ug.group_id \n'
        f"            JOIN events e ON e.profile_id_interact = p.profile_id \n"
        f"        WHERE\n"
        f"            DATE(e.created_at) = CURRENT_DATE AND e.issue = 'OK'\n"
        f"        GROUP BY\n"
        f"            g.group_id \n"
        f"        HAVING\n"
        f"            COUNT(DISTINCT p.profile_id) > 0\n"
        f"    ),\n"
        f"    Receivers AS (\n"
        f"        SELECT\n"
        f"            g.group_id,\n"
        f"            COUNT(e.profile_id) AS total_clicks_receiver\n"
        f"        FROM\n"
        f'            "public".user u \n'
        f"            JOIN profiles p ON u.user_id = p.owner\n"
        f"            JOIN user_group ug ON ug.user_id = u.user_id \n"
        f'            JOIN "groups" g ON g.group_id = ug.group_id \n'
        f"            JOIN events e ON e.profile_id  = p.profile_id \n"
        f"        WHERE\n"
        f"            DATE(e.created_at) = CURRENT_DATE AND e.issue = 'OK'\n"
        f"        GROUP BY\n"
        f"            g.group_id \n"
        f"        HAVING\n"
        f"            COUNT(DISTINCT p.profile_id) > 0\n"
        f"    )\n"
        f"    -- Step 2: Update groups table with the click_count and receiver_count\n"
        f'    UPDATE "groups" AS g\n'
        f"    SET click_count = COALESCE(c.total_clicks_giver, 0),\n"
        f"        receiver_count = COALESCE(r.total_clicks_receiver, 0)\n"
        f"    FROM Clicks c\n"
        f"    JOIN Receivers r ON c.group_id = r.group_id\n"
        f"    WHERE g.group_id = c.group_id;\n"
        f"    "
    )

    try:
        _logger.info('Update click count ok')
        # Execute the raw SQL query
        db.session.execute(sql_query)
        db.session.commit()
    except Exception as e:
        # Rollback transaction if an error occurs
        db.session.rollback()
        _logger.error(e)


def reset_click_count(teams_id):
    migration_services.set_search_path(teams_id)
    # Update operation to set click_count to zero for all profiles
    try:
        stmt = update(Profiles).values(click_count=0, comment_count=0, like_count=0)
        db.session.execute(stmt)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        _logger.error(e)
