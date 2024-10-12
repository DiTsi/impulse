from app.im.users import UndefinedUser
from app.logging import logger


def generate_user_groups(user_groups_dict=None, users=None):
    user_groups = dict()
    if user_groups_dict:
        logger.info(f'Creating user_groups')
        for name in user_groups_dict.keys():
            user_names = user_groups_dict[name]['users']
            user_objects = list()
            for user_name in user_names:
                user_object = users.get(user_name, UndefinedUser(user_name))
                user_objects.append(user_object)
            user_groups[name] = UserGroup(name, user_objects)
    else:
        logger.info(f'No user_groups defined in impulse.yml. Continue with empty user_groups')
    return user_groups


class UserGroup:
    def __init__(self, name, users):
        self.name = name
        self.users = users
