"""first init database

Revision ID: d8f1b0f2c0e0
Revises: 
Create Date: 2024-01-11 23:05:11.205375

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Inspector

# revision identifiers, used by Alembic.
revision = '91dede4a905b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names(schema='public')
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\" SCHEMA public;")
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('auth_token_blacklist',
                    sa.Column('token_id', sa.String(128), nullable=False),
                    sa.PrimaryKeyConstraint('token_id')
                    )
    if 'teams' not in tables:
        op.create_table('teams',
                        sa.Column('teams_id', sa.String(128),
                                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
                        sa.Column('teams_name', sa.String(length=256), nullable=False),
                        sa.Column('teams_code', sa.String(length=256), nullable=True),
                        sa.Column('owner', sa.String(128), nullable=True),
                        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                        sa.Column('is_disabled', sa.Boolean(), server_default='false', nullable=True),
                        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=True),
                        sa.PrimaryKeyConstraint('teams_id'),
                        schema='public'
                        )
    op.create_table('robot',
                    sa.Column('robot_id', sa.String(128), server_default=sa.text('uuid_generate_v4()'),
                              nullable=False),
                    sa.Column('robot_code', sa.String(length=30), nullable=True),
                    sa.Column('nick_name', sa.String(length=30), nullable=True),
                    sa.Column('status', sa.String(length=30), nullable=True),
                    sa.Column('modified_by', sa.BigInteger(), nullable=True),
                    sa.Column('downtime_cost', sa.Numeric(precision=5, scale=2), nullable=True),
                    sa.Column('activation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                              nullable=True),
                    sa.Column('deactivation_date', sa.DateTime(timezone=True), nullable=True),
                    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
                    sa.Column('deploy_va_engine', sa.Boolean(), server_default='false', nullable=True),
                    sa.Column('va_engine_status', sa.String(length=128), server_default='', nullable=False),
                    sa.Column('robot_ip_address', postgresql.INET(), nullable=True),
                    sa.Column('robot_computer_id', sa.String(length=30), nullable=True),
                    sa.Column('external_url', sa.String(length=255), nullable=True),
                    sa.Column('rosbridge_url', sa.String(length=255), nullable=True),
                    sa.Column('camerafeed_url', sa.String(length=255), nullable=True),
                    sa.Column('robot_url', sa.String(length=255), nullable=True),
                    sa.Column('aws_channel_arn', sa.String(length=500), nullable=True),
                    sa.Column('aws_kinesis_video_stream', sa.String(length=512), nullable=True),
                    sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
                    sa.Column('rosbridge_support', sa.Boolean(), server_default='false', nullable=False),
                    sa.Column('modified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                              nullable=True),
                    sa.Column('last_heartbeat_at', sa.DateTime(), nullable=True),
                    sa.Column('last_health_update', sa.DateTime(), nullable=True),
                    sa.Column('pilot_config', postgresql.JSONB(astext_type=sa.Text()),
                              server_default='{"roboops":{"map":{"topicId":"MAP","topicType":"nav_msgs/OccupancyGrid","topicName":"/map"},"laser_scan":{"topicId":"LASER_SCAN","topicType":"sensor_msgs/LaserScan","topicName":"/scan"},"move_base_goal":{"topicId":"MOVE_BASE_GOAL","topicType":"geometry_msgs/PoseStamped","topicName":"/move_base_simple/goal"},"navigation_plan":{"topicId":"NAVIGATION_PLAN","topicType":"nav_msgs/Path","topicName":"/move_base/NavfnROS/plan"},"navigation_stop":{"topicId":"NAVIGATION_STOP","topicType":"actionlib_msgs/GoalID","topicName":"/move_base/cancel","topicMode": "PUBLISH"},"navigation_status":{"topicId":"NAVIGATION_STATUS","topicType":"actionlib_msgs/GoalStatusArray","topicName":"/move_base/status","topicMode":"PUBLISH"},"navigation_result":{"topicId":"NAVIGATION_RESULT","topicType":"move_base_msgs/MoveBaseActionResult","topicName":"/move_base/result","topicMode":"PUBLISH"},"localization_pose":{"topicId":"LOCALIZATION_POSE","topicType":"geometry_msgs/PoseWithCovarianceStamped","topicName":"/initialpose"},"occupancyGrid":{"localCostMap":false,"globalCostMap":false,"laser":true}}}',
                              nullable=True),
                    sa.Column('status_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.Column('init_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.PrimaryKeyConstraint('robot_id')
                    )
    if 'role_permission_mapping_log' not in tables:
        op.create_table('role_permission_mapping_log',
                        sa.Column('role_id', sa.String(128), nullable=False),
                        sa.Column('permission_id', sa.String(128), nullable=False),
                        sa.Column('deactivation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                                  nullable=True),
                        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
                        schema='public'
                        )
    if 'user' not in tables:
        op.create_table('user',
                        sa.Column('user_id', sa.String(128), server_default=sa.text('uuid_generate_v4()'),
                                  nullable=False),
                        sa.Column('username', sa.String(length=256), nullable=False),
                        sa.Column('email', sa.String(length=256), nullable=True),
                        sa.Column('password', sa.String(length=512), nullable=True),
                        sa.Column('first_name', sa.String(length=128), nullable=True),
                        sa.Column('last_name', sa.String(length=128), nullable=True),
                        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                        sa.Column('default_page', sa.String(length=128), nullable=True),
                        sa.Column('is_disabled', sa.Boolean(), server_default='false', nullable=True),
                        sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
                        sa.Column('mfa_enabled', sa.Boolean(), server_default='false', nullable=True),
                        sa.Column('mfa_secret', postgresql.BYTEA(), nullable=True),
                        sa.Column('phone_number', sa.String(length=128), nullable=True),
                        sa.Column('is_email_verified', sa.Boolean(), server_default='false', nullable=True),
                        sa.Column('country_id', sa.String(128), nullable=True),
                        sa.Column('last_active_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                        sa.PrimaryKeyConstraint('user_id'),
                        sa.UniqueConstraint('username'),
                        schema='public'
                        )

    # op.create_table('user_details',
    #                 sa.Column('user_id', sa.String(128), server_default=sa.text('uuid_generate_v4()'),
    #                           nullable=False),
    #                 sa.Column('username', sa.String(length=256), nullable=False),
    #                 sa.Column('email', sa.String(length=256), nullable=True),
    #                 sa.Column('password', sa.String(length=512), nullable=True),
    #                 sa.Column('first_name', sa.String(length=128), nullable=True),
    #                 sa.Column('last_name', sa.String(length=128), nullable=True),
    #                 sa.Column('default_page', sa.String(length=128), nullable=True),
    #                 sa.Column('is_disabled', sa.Boolean(), server_default='false', nullable=True),
    #                 sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
    #                 sa.Column('phone_number', sa.String(length=128), nullable=True),
    #                 sa.Column('is_email_verified', sa.Boolean(), server_default='false', nullable=True),
    #                 sa.Column('country_id', sa.String(128), nullable=True),
    #                 sa.Column('added_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    #                 sa.PrimaryKeyConstraint('user_id'),
    #                 sa.UniqueConstraint('username')
    #                 )
    if 'user_permissions' not in tables:
        op.create_table('user_permissions',
                        sa.Column('permission_id', sa.String(128),
                                  server_default=sa.text('uuid_generate_v4()'), nullable=False),
                        sa.Column('permission_name', sa.String(length=128), nullable=True),
                        sa.Column('description', sa.String(length=1024), nullable=True),
                        sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                        sa.Column('permission_value', sa.String(length=512), nullable=True),
                        sa.PrimaryKeyConstraint('permission_id'),
                        schema='public'
                        )
    if 'user_role' not in tables:
        op.create_table('user_role',
                        sa.Column('role_id', sa.String(128), server_default=sa.text('uuid_generate_v4()'),
                                  nullable=False),
                        sa.Column('role_name', sa.String(length=32), nullable=True),
                        sa.Column('role_description', sa.String(length=1024), nullable=True),
                        sa.Column('created_on', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                        sa.Column('is_deletable', sa.Boolean(), nullable=True),
                        sa.PrimaryKeyConstraint('role_id'),
                        schema='public'
                        )
    if 'user_role_mapping_log' not in tables:
        op.create_table('user_role_mapping_log',
                        sa.Column('user_id', sa.String(128), nullable=False),
                        sa.Column('role_id', sa.String(128), nullable=False),
                        sa.Column('teams_id', sa.String(128), nullable=False),
                        sa.Column('deactivation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                                  nullable=True),
                        sa.PrimaryKeyConstraint('user_id', 'role_id', 'teams_id'),
                        schema='public'
                        )
    op.create_table('mission',
                    sa.Column('mission_id', sa.String(128), server_default=sa.text('uuid_generate_v4()'),
                              nullable=False, comment='Unique identifier for mission(Primary Key)'),
                    sa.Column('mission_name', sa.String(length=256), nullable=True, comment='Name of the mission'),
                    sa.Column('robot_id', sa.String(128), nullable=False,
                              comment='Unique identifier for robot owning the mission(Foreign Key)'),
                    sa.Column('mission_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                              comment='JSON for mission'),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True,
                              comment='Timestamp indicating when the record was soft deleted'),
                    sa.ForeignKeyConstraint(['robot_id'], ['robot.robot_id'], ),
                    sa.PrimaryKeyConstraint('mission_id')
                    )
    if 'role_permission_mapping' not in tables:
        op.create_table('role_permission_mapping',
                        sa.Column('role_id', sa.String(128), nullable=False),
                        sa.Column('permission_id', sa.String(128), nullable=False),
                        sa.ForeignKeyConstraint(['permission_id'], ['user_permissions.permission_id'], ),
                        sa.ForeignKeyConstraint(['role_id'], ['user_role.role_id'], ),
                        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
                        sa.UniqueConstraint('role_id', 'permission_id', name='_role_permission_uc'),
                        schema='public'
                        )
    if 'user_teams_mapping' not in tables:
        op.create_table('user_teams_mapping',
                        sa.Column('user_id', sa.String(128), nullable=False),
                        sa.Column('teams_id', sa.String(128), nullable=False),
                        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=True),
                        sa.ForeignKeyConstraint(['teams_id'], ['teams.teams_id'], ),
                        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
                        sa.PrimaryKeyConstraint('user_id', 'teams_id'),
                        sa.UniqueConstraint('user_id', 'teams_id', name='_user_teams_uc'),
                        schema='public'
                        )
    if 'user_password_reset_token' not in tables:
        op.create_table('user_password_reset_token',
                        sa.Column('token', sa.String(length=512), nullable=False,
                                  comment='base64 URL encoded token for password reset'),
                        sa.Column('user_id', sa.String(128), nullable=False,
                                  comment='User ID that generated the token'),
                        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True,
                                  comment='Timestamp for creation of token'),
                        sa.Column('used_at', sa.DateTime(), nullable=True,
                                  comment='Timestamp for use/consumption of token'),
                        sa.Column('is_valid', sa.Boolean(), server_default='true', nullable=True,
                                  comment='Boolean check if token is valid'),
                        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
                        sa.PrimaryKeyConstraint('token'),
                        schema='public'
                        )
    op.create_table('user_preference',
                    sa.Column('preference_id', sa.String(128),
                              server_default=sa.text('uuid_generate_v4()'), nullable=False),
                    sa.Column('user_id', sa.String(128), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                    sa.Column('default_page', sa.String(length=128), nullable=True),
                    sa.Column('is_disabled', sa.Boolean(), server_default='false', nullable=True),
                    sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
                    sa.Column('added_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
                    sa.Column('grafana_url', sa.String(length=128), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
                    sa.PrimaryKeyConstraint('preference_id')
                    )
    if 'user_role_mapping' not in tables:
        op.create_table('user_role_mapping',
                        sa.Column('user_id', sa.String(128), nullable=False),
                        sa.Column('role_id', sa.String(128), nullable=False),
                        sa.Column('teams_id', sa.String(128), nullable=False),
                        sa.ForeignKeyConstraint(['role_id'], ['user_role.role_id'], ),
                        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
                        sa.ForeignKeyConstraint(['teams_id'], ['teams.teams_id'], ),
                        sa.PrimaryKeyConstraint('user_id', 'role_id'),
                        sa.UniqueConstraint('user_id', 'role_id', 'teams_id', name='_user_role_team_uc'),
                        schema='public'
                        )
    op.create_table('mission_schedule',
                    sa.Column('schedule_id', sa.String(128),
                              server_default=sa.text('uuid_generate_v4()'), nullable=False,
                              comment='Unique identifier for schedule(Primary Key)'),
                    sa.Column('robot_id', sa.String(128), nullable=False,
                              comment='Unique identifier for robot owning the schedule(Foreign Key)'),
                    sa.Column('mission_id', sa.String(128), nullable=False,
                              comment='Unique identifier for mission(Foreign Key)'),
                    sa.Column('schedule_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                              comment='JSON for schedule'),
                    sa.Column('timezone', sa.TEXT(), nullable=True, comment='Timezone for schedule'),
                    sa.Column('last_updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True,
                              comment='Timestamp indicating when this was last updated'),
                    sa.Column('start_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False,
                              comment='Schedule will be available for fetch or search after this date'),
                    sa.Column('end_timestamp', sa.DateTime(), nullable=True,
                              comment='Timestamp indicating when the scheduled is supposed to end'),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True,
                              comment='Timestamp indicating when the record was soft deleted'),
                    sa.ForeignKeyConstraint(['mission_id'], ['mission.mission_id'], ),
                    sa.ForeignKeyConstraint(['robot_id'], ['robot.robot_id'], ),
                    sa.PrimaryKeyConstraint('schedule_id')
                    )
    op.create_table('mission_instance',
                    sa.Column('mission_instance_id', sa.String(128),
                              server_default=sa.text('uuid_generate_v4()'), nullable=False,
                              comment='Unique identifier for mission_instance(Primary Key)'),
                    sa.Column('mission_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                              comment='JSON for mission'),
                    sa.Column('issues_recorded', postgresql.JSONB(astext_type=sa.Text()), nullable=True,
                              comment='Issues for the mission'),
                    sa.Column('start_timestamp', sa.DateTime(), nullable=True, comment='Start time for the mission'),
                    sa.Column('end_timestamp', sa.DateTime(), nullable=True, comment='End time for the mission'),
                    sa.Column('last_updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True,
                              comment='Timestamp indicating when this was last updated'),
                    sa.Column('is_cancelled', sa.Boolean(), server_default='false', nullable=True,
                              comment='Boolean to check for cancelled missions'),
                    sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=True,
                              comment='Boolean to check for deleted missions'),
                    sa.Column('is_complete', sa.Boolean(), server_default='false', nullable=True,
                              comment='Boolean to check status of the mission completion'),
                    sa.Column('is_scheduled', sa.Boolean(), server_default='false', nullable=True,
                              comment='Boolean to check scheduled mission instance'),
                    sa.Column('required_intervention', sa.Boolean(), server_default='false', nullable=True,
                              comment='Boolean to check for interventions'),
                    sa.Column('success_category', sa.String(length=15), server_default='', nullable=True,
                              comment='String for categorising missions'),
                    sa.Column('analysis_complete', sa.Boolean(), server_default='false', nullable=True,
                              comment='Boolean to check for mission analysis status'),
                    sa.Column('robot_id', sa.String(128), nullable=False,
                              comment='Unique identifier for robot(Foreign Key)'),
                    sa.Column('mission_id', sa.String(128), nullable=True,
                              comment='Unique identifier for mission(Foreign Key)'),
                    sa.Column('schedule_id', sa.String(128), nullable=True,
                              comment='Unique identifier for mission_schedule(Foreign Key)'),
                    sa.Column('loop_count', sa.Integer(), nullable=True,
                              comment='Looping count for mission in schedule'),
                    sa.Column('task_last_updated_at', sa.DateTime(), nullable=True,
                              comment='Timestamp indicating when the task was last updated'),
                    sa.ForeignKeyConstraint(['mission_id'], ['mission.mission_id'], ),
                    sa.ForeignKeyConstraint(['robot_id'], ['robot.robot_id'], ),
                    sa.ForeignKeyConstraint(['schedule_id'], ['mission_schedule.schedule_id'], ),
                    sa.PrimaryKeyConstraint('mission_instance_id')
                    )
    op.execute(
        "CREATE OR REPLACE VIEW user_details AS SELECT u.user_id,u.username,u.email,u.password,u.first_name,u.last_name, u.phone_number, up.preference_id, up.default_page,up.is_disabled, up.notifications_enabled, up.modified_at  FROM \"user\" u JOIN user_preference up ON up.user_id=u.user_id;")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP VIEW IF EXISTS user_details;")
    op.drop_table('mission_instance')
    op.drop_table('mission_schedule')
    op.drop_table('user_role_mapping')
    op.drop_table('user_preference')
    op.drop_table('user_password_reset_token')
    op.drop_table('user_teams_mapping')
    op.drop_table('role_permission_mapping')
    op.drop_table('mission')
    op.drop_table('user_role_mapping_log')
    op.drop_table('user_role')
    op.drop_table('user_permissions')
    op.drop_table('user_details')
    op.drop_table('user')
    op.drop_table('role_permission_mapping_log')
    op.drop_table('robot')
    op.drop_table('teams')
    op.drop_table('auth_token_blacklist')
    # ### end Alembic commands ###
