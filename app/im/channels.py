from app.logging import logger


def check_channels(channels_list, channels_config, default_channel):
    logger.info('Check all channels defined')
    default_channel_id = channels_config.get(default_channel, {}).get('id')
    default_channel_thread_id = channels_config.get(default_channel, {}).get('thread_channel_id')

    for channel in channels_list:
        channel_config = channels_config.get(channel, {})
        channel_id = channel_config.get('id')

        if not channel_id:
            logger.warning(f'.. channel {channel} not defined or has no valid \'id\'. Using default channel instead')
            channels_config[channel] = {'id': default_channel_id}
            if default_channel_thread_id:
                channels_config[channel]['thread_channel_id'] = default_channel_thread_id

    logger.info('.. done')
    return channels_config
