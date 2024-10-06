def telegram_get_create_thread_payload(channel_id, body, header, status_icons, status):
    payload = {
        'chat_id': channel_id,
        'text': f'{status_icons} {status} {header}\n{body}',
        'parse_mode': 'MarkdownV2'
    }
    return payload
