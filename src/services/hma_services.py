import os
import requests
import logging
from src.services import setting_services, profiles_services

base_url = os.environ.get("HMA_ENDPOINTS")
appVersion = 3049

_logger = logging.getLogger()


def authenticate(username, password):
    """Authenticate and get a token."""
    url = f"{base_url}/auth"
    auth = (username, password)
    data = {"version": appVersion}
    response = requests.post(url, auth=auth, data=data)
    if response.status_code == 200 and response.json()["code"] == 1:
        return response.json()["result"]["token"]
    raise Exception("HMA Account is required")


def get_account_info(token):
    """Get account information."""
    url = f"{base_url}/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def create_marco_browser_profile(token, data):
    """Create a Marco browser profile."""
    url = f"{base_url}/browser/marco"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 402:
        raise Exception("HMA Account limit excelled, please contact your administrator")
    elif response.status_code == 200:
        return response.json()
    raise Exception("Please contact your administrator")


def delete_browser_profile(profile_id, user_id, device_id):
    settings = setting_services.get_settings_by_user_device(user_id, device_id)
    if not settings:
        raise Exception("User settings not found")
    settings = settings["settings"]
    hma_account = settings.get("hideMyAccAccount")
    hma_password = settings.get("hideMyAccPassword")
    hma_token = authenticate(hma_account, hma_password)
    """Delete a browser profile."""
    url = f"{base_url}/browser/{profile_id}"
    headers = {"Authorization": f"Bearer {hma_token}"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 404:
        return True
    if response.json()["code"] == 1:
        return True
    raise Exception("Please contact your administrator, delete profile failed")


def list_browser_profiles(token):
    """List browser profiles."""
    url = f"{base_url}/browser?appVersion={appVersion}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def get_browser_data(token, hma_profile_id, tz_data):
    """Get browser data for a specific profile."""
    url = f"{base_url}/browser/marco/data/{hma_profile_id}"
    headers = {"Authorization": f"Bearer {token}"}
    timezone_data = {"tz": tz_data}
    response = requests.post(url, headers=headers, json=timezone_data)
    if response.status_code == 200:
        return True, response.json()
    if response.status_code == 404:
        return False, f"Account not found error ${hma_profile_id}"
    return False, "HMA error can not get proxy timezone data"


def update_browser_profile(token, profile_id, data):
    """Update a browser profile."""
    url = f"{base_url}/browser/{profile_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(url, headers=headers, json=data)
    return response.json()


def list_team_members(token, team_name):
    """List team members."""
    url = f"{base_url}/members/team/{team_name}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


def create_team_member(token, team_name, data):
    """Create a team member."""
    url = f"{base_url}/members/team/{team_name}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def update_team_member(token, team_name, member_email, data):
    """Update profiles for a team member."""
    url = f"{base_url}/members/team/{team_name}/{member_email}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(url, headers=headers, json=data)
    return response.json()


def delete_team_member(token, team_name, member_email):
    """Delete a team member."""
    url = f"{base_url}/members/team/{team_name}/{member_email}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(url, headers=headers)
    return response.json()


def create_hma_profile(username, device_id, user_id):
    settings = setting_services.get_settings_by_user_device(user_id, device_id)
    if not settings or "settings" not in settings.keys():
        raise Exception("Vui lòng cài đặt hệ thống")
    settings = settings["settings"]
    browser_type = settings.get("browserType")
    if browser_type != "hideMyAcc" or username == "":
        return ""

    browser_version = settings.get("browserVersion")
    if not browser_version:
        browser_version = 119
    hma_account = settings.get("hideMyAccAccount")
    hma_password = settings.get("hideMyAccPassword")
    hma_token = authenticate(hma_account, hma_password)
    data = {
        "name": username,
        "os": "win",
        "uploadCookiesToServer": True,
        "uploadBookmarksToServer": True,
        "uploadHistoryToServer": True,
        "uploadLocalStorageToServer": True,
        "resolution": "1920x1080",
        "canvasMode": "noise",
        "clientRectsMode": "noise",
        "audioContextMode": "noise",
        "webGLImageMode": "noise",
        "webGLMetadataMode": "noise",
        "browserVersion": int(browser_version),
        "versionCode": appVersion,
    }
    hma_exist = get_hma_profiles(hma_token)
    for item in hma_exist["result"]:
        if (
            username
            and item.get("name", "").lower().strip() == username.lower().strip()
        ):
            return item["id"]
    response = create_marco_browser_profile(hma_token, data)
    if response["code"] == 1:
        profile_id = response["result"]["id"]
        return profile_id
    return ""


def clear_unused_resourced(device_id, user_id):
    try:
        settings = setting_services.get_settings_by_user_device(user_id, device_id)
        if not settings or "settings" not in settings.keys():
            return False
        settings = settings.get("settings")
        hma_account = settings.get("hideMyAccAccount")
        hma_password = settings.get("hideMyAccPassword")
        hma_token = authenticate(hma_account, hma_password)

        profiles = profiles_services.get_all_profiles(page=None, per_page=None)
        profiles = profiles.get("profiles", [])
        hma_profile_ids = [profile["hma_profile_id"] for profile in profiles]
        hma_exist = get_hma_profiles(hma_token)
        for item in hma_exist["result"]:
            if item["id"] not in hma_profile_ids:
                url = f"{base_url}/browser/{item['id']}"
                headers = {"Authorization": f"Bearer {hma_token}"}
                name = item["name"]
                _logger.info(f"found unused profile: {name}")
                requests.delete(url, headers=headers)
    except Exception as ex:
        _logger.exception(ex)


def get_hma_profiles(hma_token):
    url = f"{base_url}/browser?appVersion={appVersion}"
    headers = {"Authorization": f"Bearer {hma_token}"}
    response = requests.get(url, headers=headers)
    if response.ok:
        return response.json()
    raise Exception("Please check your HMA account")


def get_tz_data(profile_data):
    try:
        proxy = profile_data.proxy
        if not proxy:
            raise Exception("Proxy not found exception")
        splitter = proxy.split(":")
        if len(splitter) == 4:
            host, port, username, passowrd = splitter
            proxy = f"{username}:{passowrd}@{host}:{port}"
        response = requests.get("https://time.hidemyacc.com/", proxies={"http": proxy})
        return response.json()
    except Exception as ex:
        _logger.exception(ex)
        return {}
