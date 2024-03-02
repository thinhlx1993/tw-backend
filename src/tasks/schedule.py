from src import db, celery
from src.views.groups import GroupViews
from src.models import Groups
from sqlalchemy import update


@celery.task
def update_click(*args, **kwargs):
    teams_id = "01cd2da0-3fe2-4335-a689-1bc482ad7c52"
    print("Update start")
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
            stmt = (
                update(Groups)
                .where(Groups.group_id == item.group_id)
                .values(
                    click_count=item.total_clicks_giver,
                    receiver_count=item.total_clicks_receiver,
                    profile_receiver_count=item.profile_receiver,
                    profile_giver_count=item.profile_giver,
                )
            )

            db.session.execute(stmt)
            db.session.flush()
        db.session.commit()
        print("Update ok")
        return True


@celery.task
def reset_click(*args, **kwargs):
    teams_id = "01cd2da0-3fe2-4335-a689-1bc482ad7c52"
    with db.app.app_context():
        db.session.execute("SET search_path TO public, 'cs_" + teams_id + "'")
        # Update operation to set click_count to zero for all profiles
        sql_query = """
                    UPDATE profiles
                    SET click_count = 0,
                        comment_count = 0,
                        like_count = 0;
                    """
        db.session.execute(sql_query)
        db.session.flush()
        db.session.commit()
        print("reset_click_count OK")
        return True
