from sqlalchemy import func, cast, or_, Numeric, Text
from src import db
from src.models import User, Profiles


def get_dashboard_data():
    user_count = User.query.count()
    profiles_count = Profiles.query.count()

    verified_profiles_count = (
        db.session.query(func.count(Profiles.username))
        .filter(
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "true",
            cast(Profiles.profile_data["monetizable"], Text) == "false",
            Profiles.main_profile == False,
        )
        .scalar()
    )

    unverified_profiles_count = (
        db.session.query(func.count(Profiles.username))
        .filter(
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "false",
        )
        .scalar()
    )

    monetizable_profiles_count = (
        db.session.query(func.count(Profiles.username))
        .filter(
            Profiles.profile_data.isnot(None),
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["NotStarted", "OK"]
            ),
            Profiles.main_profile == True,
        )
        .scalar()
    )

    total_earnings_result = (
        db.session.query(
            func.coalesce(
                func.sum(cast(cast(Profiles.profile_data["earning"], Text), Numeric)), 0
            )
        )
        .filter(
            Profiles.profile_data.isnot(None), Profiles.profile_data["earning"] != None
        )
        .scalar()
    )

    users = User.query.filter_by().all()
    summaries = []
    for user in users:
        user_summary = get_summary(user.user_id)
        user_summary["username"] = user.username
        summaries.append(user_summary)
    sorted_data = sorted(
        summaries, key=lambda x: x["verified_profiles_count"], reverse=True
    )
    response_data = {
        "user_count": user_count,
        "profiles_count": profiles_count,
        "verified_profiles_count": verified_profiles_count,
        "unverified_profiles_count": unverified_profiles_count,
        "monetizable_profiles_count": monetizable_profiles_count,
        "total_earnings": float(total_earnings_result),
        "summaries": sorted_data,
    }
    return response_data


def get_summary(user_id):
    profiles_count = Profiles.query.filter(
        Profiles.owner == user_id,
    ).count()

    verified_profiles_count = (
        db.session.query(func.count(Profiles.username))
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "true",
            cast(Profiles.profile_data["monetizable"], Text) == "false",
            Profiles.main_profile == False,
        )
        .scalar()
    )

    unverified_profiles_count = (
        db.session.query(func.count(Profiles.username))
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "false",
        )
        .scalar()
    )

    monetizable_profiles_count = (
        db.session.query(func.count(Profiles.username))
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["NotStarted", "OK"]
            ),
            Profiles.main_profile == True,
        )
        .scalar()
    )

    total_earnings_result = (
        db.session.query(
            func.coalesce(
                func.sum(cast(cast(Profiles.profile_data["earning"], Text), Numeric)), 0
            )
        )
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            Profiles.profile_data["earning"] != None,
        )
        .scalar()
    )
    return {
        "profiles_count": profiles_count,
        "verified_profiles_count": verified_profiles_count,
        "unverified_profiles_count": unverified_profiles_count,
        "monetizable_profiles_count": monetizable_profiles_count,
        "total_earnings": float(total_earnings_result),
    }
