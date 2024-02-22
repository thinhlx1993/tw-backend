from src import db
from src.models import Profiles


def update_click(teams_id):
    print("update_click_count", teams_id)
    with db.app.app_context():
        db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
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
            # Execute the raw SQL query
            db.session.execute(sql_query)
            db.session.commit()
            print('Update click count ok')
        except Exception as e:
            # Rollback transaction if an error occurs
            db.session.rollback()
            print(f"update_click_count_error {e}")


def reset_click(teams_id):
    with db.app.app_context():
        db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
        # Update operation to set click_count to zero for all profiles
        try:
            stmt = update(Profiles).values(click_count=0, comment_count=0, like_count=0)
            db.session.execute(stmt)
            db.session.commit()
            print("reset_click_count OK")
        except Exception as e:
            db.session.rollback()
            print(f"reset_click_count ERROR {e}")
