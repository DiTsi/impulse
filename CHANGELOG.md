# Changelog

## v1.1.0
Changes:
- Added webhook notifications in instant messengers
- Huge refactoring
- Run using WSGI
- Fix user, user_group notifications for not existing and undefined users
- Logs refactoring

## v1.0.4
Changes:
- Fix Mattermost @mentions

## v1.0.3
Changes:
- Increase pagination limits for Mattermost API requests

## v1.0.2
Changes:
- Increase limit from 60 to 1000 for Mattermost API `/api/v4/teams/<team_id>/channels`

## v1.0.1
Changes:
- Increase limit from 100 to 1000 for Slack API `api/conversations.list`

## v1.0.0
Upgrade instructions:
- Remove `check_updates` option from `impulse.yml`
- Remove `application.message_template` option. Instead, you can use `application.template_files`
- Rename `webhook.user` to `webhook.auth`

Changes:
- New incident message structure. Contains `status_icons`, `header` and `body`
- Added template files for incident message components
- Changed `impulse.yml` format
- Fix Mattermost update payload
- New notifications format
- Mattermost buttons state fix
- Update Mattermost button payload
- Fix user_group notifications

## v0.6.0
Changes:
- Added release notes to 'update available' message
- Fix Mattermost update message functional
- Fix Mattermost user notification for user without first name
- Fix Mattermost bug when declared user not exists in Mattermost 

## v0.5.0
Changes:
- Replaced ugly Mattermost button icons
- Mattermost config now uses displayed team name
- Fix error in 'user not found' logic for Mattermost user_groups
- Fix case-sensitive team name in Mattermost incident links
- Field 'user' for Webhook is not required
