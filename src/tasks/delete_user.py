import requests

username = "thanthan101101@gmail.com"
password = "99999999"
appVersion = 3049
base_url = "https://api-tuan.hidemyacc.com"
url = f"{base_url}/auth"
auth = (username, password)
data = {"version": appVersion}
response = requests.post(url, auth=auth, data=data)
hma_access_token = response.json()["result"]["token"]

url = f"{base_url}/browser?appVersion={appVersion}"
headers = {"Authorization": f"Bearer {hma_access_token}"}
response = requests.get(url, headers=headers)
data = response.json()

for item in data["result"]:
    profile_id = item["id"]
    url = f"{base_url}/browser/{profile_id}"
    headers = {"Authorization": f"Bearer {hma_access_token}"}
    response = requests.delete(url, headers=headers)
    if response.json()["code"] == 1:
        print(f"{item['name']} Deleted ok")
