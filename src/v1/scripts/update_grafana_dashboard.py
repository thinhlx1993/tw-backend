import logging

from src import db, Config
from src.services import migration_services, teams_services
from src.services.grafana_services import (
    update_json_data_source,
    get_folder,
    update_dashboard,
    upgrade_grafana_credentials,
    update_user_default_preference,
    create_grafana_user, create_folder,
    check_folder_permissions
)


def update_grafana_dashboard(teams_id):
    """
    Perform all operations to create dashboard on grafana
    :param teams_id(uuid): Unique ID of the teams
    :param user_id(uuid): User ID of the new user
    """
    try:
        migration_services.set_search_path(teams_id)
        # Create folder for the teams
        grafana_folder_id, grafana_folder_uid = get_folder(teams_id)
        if not grafana_folder_id:
            print("Create a new folder")
            grafana_folder_id, grafana_folder_uid = create_folder(teams_id)

        # permissions = check_folder_permissions(grafana_folder_uid)
        # if len(permissions) == 1:
        #     return True

        # Update dashboard JSON
        data_source_uid = Config.GRAFANA_DATASOURCE_UID
        updated_json = update_json_data_source(data_source_uid, teams_id)
        # Create dashboard on grafana
        dashboard_url, dashboard_uid = update_dashboard(
            updated_json, grafana_folder_id, grafana_folder_uid
        )
        print(f"{teams_id}, {dashboard_url}")
        # Update Grafana Mapping table
        upgrade_grafana_credentials(teams_id, grafana_folder_id, dashboard_url)
        # Update user preference table of the new user le.thinh@kabam.ai
        # update_dashboard_user_preference(dashboard_url, "c5b6dee2-06c6-4e5c-a9cf-8d1f76cb6335")
        # org id f4c8cf83-cb30-4570-af61-5232a76ec292
        create_grafana_user(teams_id, grafana_folder_uid, dashboard_uid)
        update_user_default_preference(teams_id, dashboard_uid)
    except Exception as err:
        logging.exception(err)


# fletch all teamss
exist_teamss = []
page = 1
filters = {}
while True:
    fetch_status, fetch_data = teams_services.fetch_teams(
        page=page, per_page=1000, filters=filters
    )
    if len(fetch_data) == 0 or not fetch_status:
        break
    page += 1
    exist_teamss += fetch_data

for teams in exist_teamss:
    # Check if user already exists in the teams
    if teams["is_disabled"] or teams["is_deleted"]:
        # ignore this org
        continue

    update_grafana_dashboard(teams["teams_id"])
    db.session.flush()

db.session.commit()  # save change
