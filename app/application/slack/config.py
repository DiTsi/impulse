from config import slack_bot_user_oauth_token

url = 'https://slack.com'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {slack_bot_user_oauth_token}',
}
status_colors = {
    'firing': '#f61f1f',
    'unknown': '#c1a300',
    'resolved': '#56c15e',
    'closed': '#969696',
}
