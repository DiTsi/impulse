from app.im.mattermost.config import (mattermost_bold_text, mattermost_mention_text, mattermost_env,
                                      mattermost_admins_template_string)


class User:
    def __init__(self, name, username, first_name, last_name):
        self.name = name
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return self.username

    def mention_text(self, admins_usernames):
        if self.first_name is not None:
            text = f'➤ user {mattermost_bold_text(self.name)}: '
            text += f'{mattermost_mention_text(self.username)}'
        else:
            text = f'➤ user {mattermost_bold_text(self.name)}: '
            admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins_usernames)
            text += (f'**not found in Mattermost**\n'
                     f'➤ admins: {admins_text}')
        return text
