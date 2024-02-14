from sqlalchemy import func, cast, or_, Numeric, Text, select, text
from src import db, app
from src.models import User, Profiles
from src.services.migration_services import get_readonly_session


def get_dashboard_data():
    with get_readonly_session() as readonly_session:
        user_count = readonly_session.query(User).count()
        profiles_count = readonly_session.query(Profiles).count()

        verified_profiles_count = (
            readonly_session.query(func.count(Profiles.username))
            .filter(
                Profiles.profile_data.isnot(None),
                func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                    ["NotStarted", "ERROR"]
                ),
                Profiles.main_profile == False,
                Profiles.is_disable == False,
            )
            .scalar()
        )

        unverified_profiles_count = (
            readonly_session.query(func.count(Profiles.username))
            .filter(
                Profiles.profile_data.isnot(None),
                cast(Profiles.profile_data["verify"], Text) == "false",
                Profiles.is_disable == False,
            )
            .scalar()
        )

        monetizable_profiles_count = (
            readonly_session.query(func.count(Profiles.username))
            .filter(
                Profiles.profile_data.isnot(None),
                func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                    ["NotStarted", "OK"]
                ),
                Profiles.main_profile == True,
                Profiles.is_disable == False,
            )
            .scalar()
        )

        # payout_elements = select(
        #     [func.jsonb_array_elements(Profiles.profile_data["payouts"]).alias("element")]
        # ).lateral("payout_elements")

        # Cast each element to float and sum them up
        sql_query = """
            SELECT SUM((value::numeric)) AS total_payout
            FROM profiles p,
            LATERAL json_array_elements_text(p.profile_data->'payouts') AS value
            WHERE p.profile_data->'payouts' IS NOT NULL
            AND json_array_length(p.profile_data->'payouts') > 1
        """

        # Execute the raw SQL query
        result = readonly_session.execute(text(sql_query))
        total_payouts = result.scalar()

        users = (
            User.query.filter_by()
            .all()
        )
        summaries = []
        for user in users:
            user_summary = get_summary(user.user_id, readonly_session)
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
            "total_earnings": float(total_payouts),
            "summaries": sorted_data,
        }
        return response_data


def get_summary(user_id, readonly_session):
    profiles_count = readonly_session.query(Profiles).filter(
        Profiles.owner == user_id,
    ).count()
    if profiles_count == 0:
        return {
            "profiles_count": profiles_count,
            "verified_profiles_count": 0,
            "unverified_profiles_count": 0,
            "monetizable_profiles_count": 0,
            "total_earnings": 0,
        }

    verified_profiles_count = (
        readonly_session.query(func.count(Profiles.username))
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "true",
            cast(Profiles.profile_data["monetizable"], Text) == "false",
            Profiles.main_profile == False,
            Profiles.is_disable == False,
        )
        .scalar()
    )

    unverified_profiles_count = (
        readonly_session.query(func.count(Profiles.username))
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "false",
            Profiles.is_disable == False,
        )
        .scalar()
    )

    monetizable_profiles_count = (
        readonly_session.query(func.count(Profiles.username))
        .filter(
            Profiles.owner == user_id,
            Profiles.profile_data.isnot(None),
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["NotStarted", "OK"]
            ),
            Profiles.main_profile == True,
            Profiles.is_disable == False,
        )
        .scalar()
    )

    sql_query = f"""
        SELECT SUM((value::numeric)) AS total_payout
        FROM profiles p,
        LATERAL json_array_elements_text(p.profile_data->'payouts') AS value
        WHERE p.profile_data->'payouts' IS NOT NULL
        AND json_array_length(p.profile_data->'payouts') > 1
        AND p."owner" = '{user_id}'
    """

    # Execute the raw SQL query
    result = readonly_session.execute(text(sql_query))
    total_payouts = result.scalar()

    return {
        "profiles_count": profiles_count,
        "verified_profiles_count": verified_profiles_count,
        "unverified_profiles_count": unverified_profiles_count,
        "monetizable_profiles_count": monetizable_profiles_count,
        "total_earnings": float(total_payouts) if total_payouts else 0,
    }
