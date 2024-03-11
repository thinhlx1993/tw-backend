from src import db, celery
from src.views.groups import GroupViews
from src.models import Groups, Profiles
from sqlalchemy import update


@celery.task
def clear_dead_tuple(*args, **kwargs):
    print("VACUUM start")
    with db.app.app_context():
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".groups;')
        db.session.execute(
            'VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".auth_token_blacklist;'
        )
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".posts;')
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".tasks;')
        db.session.execute(
            'VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".mission_instance;'
        )
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".events;')
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".profiles;')
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".mission;')
        db.session.execute('VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".settings;')
        db.session.execute(
            'VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".user_group;'
        )
        db.session.execute(
            'VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".mission_schedule;'
        )
        db.session.execute(
            'VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".mission_tasks;'
        )
        db.session.execute(
            'VACUUM "cs_01cd2da0-3fe2-4335-a689-1bc482ad7c52".user_preference;'
        )
        print("VACUUM OK")


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
        profiles = db.session.query(Profiles.profile_id).filter().all()
        for profile in profiles:
            reset_profile_click.apply_async(args=[profile.profile_id])
        return True


@celery.task
def reset_profile_click(*args, **kwargs):
    try:
        profile_id = args[0] if args else None
        teams_id = "01cd2da0-3fe2-4335-a689-1bc482ad7c52"
        with db.app.app_context():
            db.session.execute("SET search_path TO public, 'cs_" + teams_id + "'")
            profile = (
                db.session.query(Profiles)
                .filter(Profiles.profile_id == profile_id)
                .first()
            )
            if profile:
                profile.click_count = 0
                profile.comment_count = 0
                profile.like_count = 0
                profile.today_post_count = 0
                db.session.flush()
                db.session.commit()
                print(f"reset_click_count {profile.username}")
                return True
            print(f"reset_click_count failed, profile not found")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
