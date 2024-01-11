from src import db
from src.models import Robot
from src.services import user_services, migration_services, grafana_services, teams_services

user_email = "jaseel@cognicept.systems"  # please change user email and user role id
role_id = "b40ee1ae-5a12-487a-98cc-b6d07238e17a"  # Kabam Super Admin

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
    if exist_in_org and robot_number == 0:
        # Check if this is user's default org
        user_org_mapping = user_services.check_user_ownership(
            user_details.get('user_id'), teams.get('teams_id'))
        if (user_org_mapping and
                str(user_org_mapping.teams_id) == teams.get('teams_id')):
            # user is owner of this org
            continue

        print("Inactivate org, Try to remove this user from this org.")
        # Remove user from this teams
        try:
            user_services.delete_user_teams_mapping(
                user_details.get('user_id'), teams.get('teams_id'))
            user_services.delete_user_preference(user_details.get('user_id'))
            user_services.delete_user_role_mapping(user_details.get('user_id'))
            db.session.flush()
            print(f"User has been removed from org {teams.get('teams_code')}")
        except Exception as err:
            print("Failed to remove user from org " + str(err))

    # this teams have robots inside, try to add this user to this org
    elif not exist_in_org and robot_number > 0:
        try:
            # Getting user preference
            user_preference = {}
            grafana_org_url = grafana_services.get_org_url(teams.get('teams_id'))
            if user_default_org:
                # User current org as users need to be added
                # to current teams

                user_preference = user_services.get_user_preference(
                    user_details['user_id'])
                if user_preference:
                    user_preference = user_services.row_to_dict(
                        user_preference)
                else:
                    user_preference = {}
                    user_preference['default_page'] = 'robotops'
                    user_preference['notifications_enabled'] = False
            else:
                user_preference['default_page'] = 'robotops'
                user_preference['notifications_enabled'] = False
            user_preference['grafana_url'] = grafana_org_url
        except Exception as err:
            print(err)
            continue
            # raise err

        # Add user to new org
        try:
            user_services.create_user_teams_mapping(
                user_details['user_id'], teams.get('teams_id'), False)
            user_services.create_user_role_mapping(
                user_details['user_id'], role_id)
            user_services.create_user_preference(
                user_details['user_id'])
            user_services.update_user_email_verification(user_details['user_id'])
            if user_details['first_name'] and user_details['last_name']:
                operator_name = (user_details['first_name'] + " "
                                 + user_details['last_name'])
            else:
                operator_name = "John Doe"
            user_services.create_operator_name(operator_name,
                                               add_id_in_zendesk=True)
            teams_name = teams.get('teams_name')
            print(f"User {user_email} has been added to org {teams_name}")
            db.session.flush()
        except Exception as err:
            print(err)
            continue

db.session.commit()  # save change
