import requests


def get_latest_tag():
    url = f"https://api.github.com/repos/DiTsi/impulse/tags"
    response = requests.get(url)

    if response.status_code == 200:
        tags = response.json()
        if tags:
            return tags[0]['name']
        else:
            return None
