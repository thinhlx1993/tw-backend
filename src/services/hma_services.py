import os
import requests
from src.services import setting_services


class HMAService:
    def __init__(self):
        self.base_url = os.environ.get("HMA_ENDPOINTS")
        self.appVersion = 3049

    def authenticate(self, username, password):
        """Authenticate and get a token."""
        url = f"{self.base_url}/auth"
        auth = (username, password)
        data = {"version": self.appVersion}
        response = requests.post(url, auth=auth, data=data)
        if response.json()['code'] == 1:
            return response.json()['result']['token']
        return ""

    def get_account_info(self, token):
        """Get account information."""
        url = f"{self.base_url}/users/me"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def create_marco_browser_profile(self, token, data):
        """Create a Marco browser profile."""
        url = f"{self.base_url}/browser/marco"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def delete_browser_profile(self, token, profile_id):
        """Delete a browser profile."""
        url = f"{self.base_url}/browser/{profile_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(url, headers=headers)
        return response.json()

    def list_browser_profiles(self, token):
        """List browser profiles."""
        url = f"{self.base_url}/browser?appVersion={self.appVersion}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def get_browser_data(self, token, profile_id):
        """Get browser data for a specific profile."""
        url = f"{self.base_url}/browser/marco/data/{profile_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def update_browser_profile(self, token, profile_id, data):
        """Update a browser profile."""
        url = f"{self.base_url}/browser/{profile_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(url, headers=headers, json=data)
        return response.json()

    def list_team_members(self, token, team_name):
        """List team members."""
        url = f"{self.base_url}/members/team/{team_name}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        return response.json()

    def create_team_member(self, token, team_name, data):
        """Create a team member."""
        url = f"{self.base_url}/members/team/{team_name}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def update_team_member(self, token, team_name, member_email, data):
        """Update profiles for a team member."""
        url = f"{self.base_url}/members/team/{team_name}/{member_email}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(url, headers=headers, json=data)
        return response.json()

    def delete_team_member(self, token, team_name, member_email):
        """Delete a team member."""
        url = f"{self.base_url}/members/team/{team_name}/{member_email}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(url, headers=headers)
        return response.json()

    def create_hma_profile(self, username, device_id, user_id):
        settings = setting_services.get_settings_by_user_device(user_id, device_id)
        settings = settings["settings"]
        browser_type = settings.get("browserType")
        if browser_type != "HideMyAcc" or username == '':
            return ""

        browser_version = settings.get("browserVersion")
        if not browser_version:
            browser_version = 119
        hma_account = settings.get("hideMyAccAccount")
        hma_password = settings.get("hideMyAccPassword")
        hma_token = self.authenticate(hma_account, hma_password)
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
            "versionCode": self.appVersion,
        }
        response = self.create_marco_browser_profile(hma_token, data)
        profile_id = response['result']['id']
        return profile_id
