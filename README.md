# IMPulse

Incident management program that creates Incidents in instant messaging app based on [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) alerts

# Instant Messangers
For now only Slack supports

## Slack

### Create bot
1.
2.


# Docker

[Slack](##Slack) section shows how to get
- SLACK_BOT_USER_OAUTH_TOKEN
- SLACK_VERIFICATION_TOKEN

```bash
docker run -p 5000:5000 -v ./data:/data -e SLACK_BOT_USER_OAUTH_TOKEN=<slack_bot_user_oauth_token> -e SLACK_VERIFICATION_TOKEN=<slack_verification_token> ghcr.io/ditsi/impulse:develop
```

# Environment

| Variable | Description | Default |
|-|-|-|
| DATA_PATH | Path to DATA directory | ./data |
| SLACK_BOT_USER_OAUTH_TOKEN | Slack Bot | |
| SLACK_VERIFICATION_TOKEN | Slack Bot | |