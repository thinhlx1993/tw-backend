from src.services import profiles_services, migration_services, mission_services
from src.log_config import _logger
from src import db


def delete_missions_schedule(mission_id, teams_id):
    _logger.debug("Start delete the mission")
    migration_services.set_search_path(teams_id)
    mission_services.delete_mission(mission_id)
    db.session.commit()
    _logger.debug("Delete mission ok")


def create_profiles(profiles, user_id, device_id, teams_id):
    migration_services.set_search_path(teams_id)
    success_number = 0
    error_number = 0
    for data in profiles:
        try:
            data["owner"] = user_id  # set owner
            data["user_access"] = user_id
            profile = profiles_services.create_profile(data, device_id, user_id)
            if profile:
                success_number += 1
                db.session.flush()
        except Exception as ex:
            _logger.exception(ex)
            error_number += 1
            # return {
            #     "message": f"Không thể tạo: {data['username']}, Đã tạo {success_number}"
            # }, 200
    # hma_services.clear_unused_resourced(device_id, user_id)
    db.session.commit()
    return True


def delete_profile(profile_id, user_id, device_id, teams_id):
    migration_services.set_search_path(teams_id)
    profiles_services.delete_profile(profile_id, user_id, device_id)
    db.session.commit()


def update_profile(profile_id, teams_id, data):
    migration_services.set_search_path(teams_id)
    profiles_services.update_profile(profile_id, data)
    db.session.commit()
