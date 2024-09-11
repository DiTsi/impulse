# IMPulse


<!-- <img src="https://docs.impulse.bot/latest/media/slack_tile.png" width="400" /> -->
![](https://docs.impulse.bot/latest/media/slack_tile.png)

Software for managing incidents in [instant messaging applications](https://docs.impulse.bot/latest/apps/) based on [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) alerts

## Features
- Slack, Mattermost [integrations](https://docs.impulse.bot/latest/apps/)
- [Twilio integration](https://docs.impulse.bot/latest/webhooks/#twilio-calls-example) using webhooks
- [Incident lifecycle](https://docs.impulse.bot/latest/concepts/#lifecycle) reduces incidents chaos
- Flexible [message structure](https://docs.impulse.bot/latest/concepts/#structure)

## Documentation
See [https://docs.impulse.bot](https://docs.impulse.bot)

## Quick Start
*Docker installation for Slack. For details see [documentation](https://docs.impulse.bot)*

1. Create bot with [instructions](https://docs.impulse.bot/latest/apps/#slack)
2. Create directories
    ```bash
    mkdir impulse impulse/config impulse/data
    cd impulse
    ```
3. Get docker-compose.yml and config
    ```bash
    wget -O docker-compose.yml https://raw.githubusercontent.com/DiTsi/impulse/master/docker-compose.yml
    wget -O config/impulse.yml https://raw.githubusercontent.com/DiTsi/impulse/master/impulse.slack.yml
    ```
4. Modify `config/impulse.yml` with actual data

5. Replace `<release_tag>` in `docker-compose.yml` to one of the [release tags](https://github.com/DiTsi/impulse/releases) and set environment variables `SLACK_BOT_USER_OAUTH_TOKEN` and `SLACK_VERIFICATION_TOKEN`

6. Run
    ```bash
    docker-compose up -d
    ```
