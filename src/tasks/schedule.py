from src import db
from src.views.groups import GroupViews
from src.models import Groups
from sqlalchemy import update

def update_click(teams_id):
    print("update_click_count", teams_id)
    with db.app.app_context():
        db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
        groups = GroupViews.query.filter().all()
        """
        total_profiles = db.Column(db.Integer)
        profile_giver = db.Column(db.Integer)
        profile_receiver = db.Column(db.Integer)
        total_clicks_giver = db.Column(db.Integer)
        total_clicks_receiver = db.Column(db.Integer)
        """
        for item in groups:
            print(f"update for {item.group_id} {item.total_clicks_giver} ")
            stmt = (
                update(Groups)
                .where(Groups.group_id == item.group_id)
                .values(
                    click_count=item.total_clicks_giver,
                    receiver_count=item.total_clicks_receiver,
                    profile_receiver_count=item.profile_receiver,
                    profile_giver_count=item.profile_giver
                )
            )

            db.session.execute(stmt)
            db.session.flush()
        db.session.commit()
        print("updated ok")


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
