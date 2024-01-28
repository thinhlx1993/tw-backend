from sqlalchemy import func, cast, or_, Numeric, Text
from src import db
from src.models import User, Profiles


def get_dashboard_data():
    user_count = User.query.count()
    profiles_count = Profiles.query.count()

    verified_profiles_count = db.session.query(func.count(Profiles.username)).filter(
        Profiles.profile_data.isnot(None),
        cast(Profiles.profile_data['verify'], Text) == 'true'
    ).scalar()

    unverified_profiles_count = db.session.query(func.count(Profiles.username)).filter(
        or_(
            Profiles.profile_data.is_(None),
            cast(Profiles.profile_data['verify'], Text) == 'false'
        )
    ).scalar()

    monetizable_profiles_count = db.session.query(func.count(Profiles.username)).filter(
        Profiles.profile_data.isnot(None),
        cast(Profiles.profile_data['monetizable'], Text) == 'true'
    ).scalar()

    total_earnings_result = db.session.query(
        func.coalesce(func.sum(cast(cast(Profiles.profile_data['earning'], Text), Numeric)), 0)
    ).filter(
        Profiles.profile_data.isnot(None),
        Profiles.profile_data['earning'] != None
    ).scalar()

    response_data = {
        "user_count": user_count,
        "profiles_count": profiles_count,
        "verified_profiles_count": verified_profiles_count,
        "unverified_profiles_count": unverified_profiles_count,
        "monetizable_profiles_count": monetizable_profiles_count,
        "total_earnings": float(total_earnings_result),
    }
    return response_data