import os

import requests


def send_mailgun_email(to, subject, text):
    MAILGUN_DOMAIN = os.environ.get("MAILGUN_DOMAIN", "")
    MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY", "")
    return requests.post(
        f'https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages',
        auth=('api', MAILGUN_API_KEY),
        data={'from': f'MeetingX Team <meetingx@soundspliter.com>',
              'to': to,
              'subject': subject,
              'text': text})
