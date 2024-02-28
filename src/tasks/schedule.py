from src import db

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
