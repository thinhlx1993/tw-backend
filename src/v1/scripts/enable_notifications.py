from src import db
from src.models import Robot
from src.services import user_services, migration_services, teams_services

user_email = "le.thinh@kabam.ai"  # please change user email and user role id

# Check user details
user_details = user_services.check_user_exists(
    username=user_email)
if not user_details:
    raise "User not found errors"
user_details = user_services.row_to_dict(user_details)


# fletch all teamss
exist_teamss = []
page = 0
while True:
    fetch_status, fetch_data = teams_services.fetch_teams(page=page, per_page=1000)
    if len(fetch_data) == 0 or not fetch_status:
        break
    page += 1
    exist_teamss += fetch_data

for teams in exist_teamss:
    # Check if user already exists in the teams
    if teams['is_disabled'] or teams['is_deleted']:
        # ignore this org
        continue

    exist_in_org = user_services.check_user_teams_mapping(user_details['user_id'],
                                                                 teams.get('teams_id'))

    # Get default org for user
    user_default_org = user_services.get_default_org(user_details['user_id'])
    if user_default_org:
        user_default_org = user_services.row_to_dict(user_default_org)

    # Set search path to current org
    migration_services.set_search_path(teams.get('teams_id'))
    # get number of robots in the teams
    robot_number = Robot.query.filter(Robot.is_deleted == False).count()
    if exist_in_org and robot_number > 0:
        user_services.update_user_notification(user_details['user_id'], True)
        print(f"Update for user {user_details['user_id']}", {teams.get('teams_name')})

db.session.commit()  # save change
