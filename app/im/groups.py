from app.im.mattermost.config import mattermost_env, mattermost_admins_template_string, \
    mattermost_users_template_string, mattermost_bold_text, mattermost_mention_text
from app.im.slack.config import slack_env, slack_bold_text, slack_mention_text
from app.im.slack.config import slack_users_template_string, slack_admins_template_string
from app.logging import logger


def generate_user_groups(user_groups_dict=None, users=None):
    user_groups = dict()
    if user_groups_dict:
        logger.info(f'Creating user_groups')
        for name in user_groups_dict.keys():
            user_names = user_groups_dict[name]['users']
            user_objects = [users.get(user_name) for user_name in user_names]
            user_groups[name] = UserGroup(name, user_objects)
        logger.info(f'user_groups created')
    else:
        logger.info(f'No user_groups defined in impulse.yml. Continue with empty user_groups')
    return user_groups


class UserGroup:
    def __init__(self, name, users):
        self.name = name
        self.users = users

    def mention_text(self, type_, admins_ids):
        if type_ == 'slack':
            text = f'➤ user_group {slack_bold_text(self.name)}: '
        else:
            text = f'➤ user_group {mattermost_bold_text(self.name)}: '
        not_found = False
        for user in self.users:
            if user is not None:
                if type_ == 'slack':
                    if user.slack_id is not None:
                        text += f'{slack_mention_text(user.slack_id)} '
                    else:
                        not_found = True
                        text += f'{user.name} (N/A) '
                else:
                    if user.username is not None:
                        text += f'{mattermost_mention_text(user.username)} '
                    else:
                        not_found = True
                        text += f'{user.name} (N/A) '
            else:
                pass
        if not_found:
            if type_ == 'slack':
                admins_text = slack_env.from_string(slack_admins_template_string).render(users=admins_ids)
            else:
                admins_text = mattermost_env.from_string(mattermost_admins_template_string).render(users=admins_ids)
            if not_found:
                text += f'\n➤ admins: _{admins_text}_'
        return text
