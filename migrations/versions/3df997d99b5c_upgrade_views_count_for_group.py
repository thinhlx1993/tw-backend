"""upgrade views count for group

Revision ID: 3df997d99b5c
Revises: 919fae805ad1
Create Date: 2024-03-09 21:37:24.109130

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3df997d99b5c"
down_revision = "919fae805ad1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE VIEW group_summary_view AS
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
                    DATE(e.created_at AT TIME ZONE 'Asia/Bangkok') = CURRENT_DATE AND e.issue = 'OK' and e.event_type = 'clickAds'
                GROUP BY
                    g.group_id 
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
                    DATE(e.created_at AT TIME ZONE 'Asia/Bangkok') = CURRENT_DATE AND e.issue = 'OK' and e.event_type = 'clickAds'
                GROUP BY
                    g.group_id 
            ),
            Profiles AS (
                SELECT
                    g.group_id,
                    COUNT(DISTINCT p.profile_id) AS total_profiles,
                    (
                        SELECT COUNT(*)
                        FROM profiles pf
                        JOIN user_group ug ON pf.owner = ug.user_id
                        WHERE pf.profile_data IS NOT NULL
                        AND (pf.profile_data->>'verify' = 'true')
                        AND (pf.profile_data->>'suspended' = 'false')
                        AND pf.main_profile = FALSE
                        AND pf.is_disable = FALSE
                        AND ug.group_id = g.group_id
                    ) AS profile_giver,
                    (
                        SELECT COUNT(*)
                        FROM profiles pf
                        JOIN user_group ug ON pf.owner = ug.user_id
                        WHERE pf.profile_data IS NOT NULL
                        AND (pf.profile_data->>'verify' = 'true')
                        AND (pf.profile_data->>'suspended' = 'false')
                        AND pf.main_profile = True
                        AND pf.is_disable = FALSE
                        AND ug.group_id = g.group_id
                    ) as profile_receiver
                FROM
                    "public".user u 
                    JOIN profiles p ON u.user_id = p.owner
                    JOIN user_group ug ON u.user_id = ug.user_id
                    JOIN "groups" g ON ug.group_id = g.group_id
                GROUP BY
                    g.group_id
            )
            select
                g.group_id,
                g.group_name,
                COALESCE(p.total_profiles, 0) AS total_profiles,
                COALESCE(p.profile_giver, 0) AS profile_giver,
                COALESCE(p.profile_receiver, 0) AS profile_receiver,
                COALESCE(c.total_clicks_giver, 0) AS total_clicks_giver,
                COALESCE(r.total_clicks_receiver, 0) AS total_clicks_receiver
            FROM
                Profiles p
            LEFT JOIN
                Clicks c ON p.group_id = c.group_id
            LEFT JOIN
                Receivers r ON p.group_id = r.group_id
            LEFT JOIN
                "groups" g ON p.group_id = g.group_id;
        """
    )


def downgrade():
    op.execute("DROP VIEW IF EXISTS group_summary_view;")
