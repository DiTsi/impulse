from config import mattermost_access_token

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {mattermost_access_token}',
}
status_colors = {
    'firing': '#f61f1f',
    'unknown': '#c1a300',
    'resolved': '#56c15e',
    'closed': '#969696',
}
