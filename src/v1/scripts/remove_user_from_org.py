from src import db
from src.services import user_services, teams_services, migration_services

user_emails = ["le.thinh@kabam.ai", "jaseel@cognicept.systems", "jakub@cognicept.systems", "michael@kabam.ai"]


# Check user details
for user_email in user_emails:
    user_details = user_services.check_user_exists(username=user_email)
    if not user_details:
        print("This user do not exist")
        continue

    user_details = user_services.row_to_dict(user_details)

    # fletch all teamss
    with open('src/v2/scripts/orgs.txt') as file:
        for teams_id in file.readlines():
            teams_id = teams_id.strip()
            teams = teams_services.get_teams(teams_id)
            if not teams or teams.is_disabled or teams.is_deleted:
                # ignore this org
                print("This teams do not exist", teams_id)
                continue

            user_id = user_details['user_id']

            try:
                # Check if user exists in teams
                if not user_services.check_user_teams_mapping(
                        user_id, teams_id):
                    print("The user does not exist in your teams!")
                    continue

                # Check if this is user's default org
                user_org_mapping = user_services.check_user_ownership(
                    user_id, teams_id)
                if (user_org_mapping and
                        str(user_org_mapping.teams_id) == teams_id):
                    print("This user is owner of the teams and \
                        cannot be removed from this teams", user_id, teams_id)
                    continue
            except Exception as err:
                print("Could not fetch user teams details", err)
                continue

            # Remove user from teams
            try:
                user_services.delete_user_teams_mapping(
                    user_id, teams_id)
                migration_services.set_search_path(teams_id)
                user_services.delete_user_preference(user_id)
                user_services.delete_user_role_mapping(user_id)
                print("User has been removed from org", teams_id)
            except Exception as err:
                print("Failed to remove user from org " + str(err))

db.session.commit()  # save change
print("finished")
