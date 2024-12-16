# IMPulse

![](https://docs.impulse.bot/latest/media/slack_tile.png)

Software for managing incidents in messengers based on [Alertmanager's](https://prometheus.io/docs/alerting/latest/alertmanager/) alerts

## Features
- Slack, Mattermost integrations
- Twilio and another integrations using [webhooks](https://docs.impulse.bot/latest/config_file/#webhooks-examples)
- [Incident lifecycle](https://docs.impulse.bot/latest/concepts/#lifecycle) reduces incidents chaos
- Flexible [message structure](https://docs.impulse.bot/latest/concepts/#structure) you can modify
- Duty shedule ([docs](https://docs.impulse.bot/latest/config_file/#schedule-chain))

## Documentation
See [https://docs.impulse.bot](https://docs.impulse.bot)

## Quick Start
*Docker installation example for Slack*

### Run

1. Use [instructions](https://docs.impulse.bot/latest/slack) to create and configure bot
2. Create directories
    ```bash
    mkdir impulse impulse/config impulse/data
    cd impulse
    ```
3. Get docker-compose.yml and config
    ```bash
    wget -O docker-compose.yml https://raw.githubusercontent.com/eslupmi/impulse/main/examples/docker-compose.yml
    wget -O config/impulse.yml https://raw.githubusercontent.com/eslupmi/impulse/main/examples/impulse.slack.yml
    ```
4. Modify `config/impulse.yml` with actual data

5. Replace `<release_tag>` in `docker-compose.yml` with latest tag from [here](https://github.com/eslupmi/impulse/releases) and set environment variables `SLACK_BOT_USER_OAUTH_TOKEN` and `SLACK_VERIFICATION_TOKEN`

6. Run
    ```bash
    docker-compose up
    ```

### Test

To ensure IMPulse works fine send test alert:

```bash
curl -XPOST -H "Content-Type: application/json" http://localhost:5000/ -d '{"receiver":"webhook-alerts","status":"firing","alerts":[{"status":"firing","labels":{"alertname":"InstanceDown4","instance":"localhost:9100","job":"node","severity":"warning"},"annotations":{"summary":"Instanceunavailable"},"startsAt":"2024-07-28T19:26:43.604Z","endsAt":"0001-01-01T00:00:00Z","generatorURL":"http://eva:9090/graph?g0.expr=up+%3D%3D+0&g0.tab=1","fingerprint":"a7ddb1de342424cb"}],"groupLabels":{"alertname":"InstanceDown"},"commonLabels":{"alertname":"InstanceDown","instance":"localhost:9100","job":"node","severity":"warning"},"commonAnnotations":{"summary":"Instanceunavailable"},"externalURL":"http://eva:9093","version":"4","groupKey":"{}:{alertname=\"InstanceDown\"}","truncatedAlerts":0}'
```
