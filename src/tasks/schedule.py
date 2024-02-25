from src import db
from src.models import Profiles


def update_click(teams_id):
    print("update_click_count", teams_id)
    with db.app.app_context():
        db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
        sql_query = """
            WITH Clicks AS (
                SELECT
                    g.group_id,
                    COUNT(e.profile_id_interact) AS total_clicks_giver
                FROM
                    "public".user u 
                    JOIN profiles p ON u.user_id = p.owner
                    JOIN user_group ug ON ug.user_id = u.user_id 
                    JOIN "groups" g ON g.group_id = ug.group_id 
                    JOIN events e ON e.profile_id_interact = p.profile_id 
                WHERE
                    DATE(e.created_at) = CURRENT_DATE AND e.issue = 'OK'
                GROUP BY
                    g.group_id 
                HAVING
                    COUNT(DISTINCT p.profile_id) > 0
            ),
            Receivers AS (
                SELECT
                    g.group_id,
                    COUNT(e.profile_id) AS total_clicks_receiver
                FROM
                    "public".user u 
                    JOIN profiles p ON u.user_id = p.owner
                    JOIN user_group ug ON ug.user_id = u.user_id 
                    JOIN "groups" g ON g.group_id = ug.group_id 
                    JOIN events e ON e.profile_id  = p.profile_id 
                WHERE
                    DATE(e.created_at) = CURRENT_DATE AND e.issue = 'OK'
                GROUP BY
                    g.group_id 
                HAVING
                    COUNT(DISTINCT p.profile_id) > 0
            )
            -- Step 2: Update groups table with the click_count and receiver_count
            UPDATE "groups" AS g
            SET
                click_count = COALESCE(c.total_clicks_giver, 0),
                receiver_count = COALESCE(r.total_clicks_receiver, 0)
            FROM
                Clicks c
                LEFT JOIN Receivers r ON c.group_id = r.group_id
            WHERE
                g.group_id = c.group_id;
        
        """

        try:
            # Execute the raw SQL query
            db.session.execute(sql_query)
            db.session.commit()
            print("Update click count ok")
        except Exception as e:
            # Rollback transaction if an error occurs
            db.session.rollback()
            print(f"update_click_count_error {e}")


def reset_click(teams_id: str):
    with db.app.app_context():
        db.session.execute("SET search_path TO public, 'cs_" + teams_id + "'")
        # Update operation to set click_count to zero for all profiles
        try:
            sql_query = """
            UPDATE profiles
            SET click_count = 0,
                comment_count = 0,
                like_count = 0;
            """
            db.session.execute(sql_query)
            db.session.commit()
            print("reset_click_count OK")
        except Exception as e:
            db.session.rollback()
            print(f"reset_click_count ERROR {e}")
