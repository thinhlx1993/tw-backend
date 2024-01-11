from flask_restx import reqparse, inputs


page_parser = reqparse.RequestParser()
page_parser.add_argument(
    'page', type=int, help='Page number to be displayed',
    location='args', required=False, default=0)
page_parser.add_argument(
    'per_page', type=int, required=False,
    help='per_page value to be added', location='args', default=10)
page_parser.add_argument('search', type=str, required=False,
                         help='Field to be search', location='args', default="")
