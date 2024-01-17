import os
# import logging
# from logging.config import dictConfig

# Config app logging
# dictConfig(
#     {
#         'version': 1,
#         'formatters': {
#             'default': {
#                 'format': '[%(asctime)s] [%(levelname)s] - [%(name)s] - [%(threadName)s]: %(message)s',
#             }
#         },
#         'handlers': {
#             'console': {
#                 'class': 'logging.StreamHandler',
#                 'stream': 'ext://flask.logging.wsgi_errors_stream',
#                 'formatter': 'default',
#                 'level': os.environ['LOG_LEVEL'],
#             }
#         },
#         'root': {'level': os.environ['LOG_LEVEL'], 'handlers': ['console']},
#     }
# )

# Disable debug logs from some noisy packages
# logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
# logging.getLogger('botocore').setLevel(logging.ERROR)
# logging.getLogger('werkzeug').setLevel(logging.ERROR)
# logging.getLogger('sentry').setLevel(logging.ERROR)
