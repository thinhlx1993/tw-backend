from flask_restx import reqparse, inputs

page_parser = reqparse.RequestParser()
page_parser.add_argument(
    "page", type=int, help="Page number to be displayed", location="args", default=1
)
page_parser.add_argument(
    "per_page", type=int, default=50, help="per_page value to be added", location="args"
)
page_parser.add_argument(
    "sort_by", type=str, help="Field to be sorted", location="args"
)
page_parser.add_argument("search", type=str, help="Search username", location="args")
page_parser.add_argument(
    "sort_order", type=str, choices=("asc", "desc"), help="asc or desc", location="args"
)
page_parser.add_argument(
    "filter", type=str, help="The filters to be applied to function", location="args"
)

date_page_parser = page_parser.copy()
date_page_parser.add_argument(
    "start_date",
    type=inputs.date_from_iso8601,
    required=True,
    help="start date in format YYYY-MM-DD",
    location="args",
)
date_page_parser.add_argument(
    "end_date",
    type=inputs.date_from_iso8601,
    help="end date in format YYYY-MM-DD",
    location="args",
)

profile_page_parser = page_parser.copy()
profile_page_parser.add_argument(
    "group_id", type=str, help="Search by group", location="args"
)

filter_parser = reqparse.RequestParser()
filter_parser.add_argument(
    "filter", type=str, help="The filters to be applied to function", location="args"
)

date_parser = reqparse.RequestParser()
date_parser.add_argument(
    "start_date",
    type=inputs.date_from_iso8601,
    required=True,
    help="start date in format YYYY-MM-DD",
    location="args",
)
date_parser.add_argument(
    "end_date",
    type=inputs.date_from_iso8601,
    help="end date in format YYYY-MM-DD",
    location="args",
)
date_parser.add_argument(
    "filter", type=str, help="The filters to be applied to function", location="args"
)


# Parser for paginated search of rosout logs
ros_event_parser = reqparse.RequestParser()
ros_event_parser.add_argument(
    "start_date",
    type=inputs.datetime_from_iso8601,
    help="start datetime in ISO 8601 format like 2021-05-03T13:56:20",
    location="args",
)
ros_event_parser.add_argument(
    "end_date",
    type=inputs.datetime_from_iso8601,
    help="end datetime in ISO 8601 format like 2021-05-03T13:56:20",
    location="args",
)
ros_event_parser.add_argument(
    "sort_order", type=str, choices=("asc", "desc"), help="asc or desc", location="args"
)
ros_event_parser.add_argument(
    "robot_id", type=str, help="robot id to fetch logs for", location="args"
)
ros_event_parser.add_argument(
    "property_id", type=str, help="property id to fetch logs for", location="args"
)
ros_event_parser.add_argument(
    "teams_id", type=str, help="teams_id to fetch logs for", location="args"
)
ros_event_parser.add_argument(
    "last_evaluated_key", type=str, help="The last item on the page", location="args"
)
ros_event_parser.add_argument(
    "limit", type=int, help="per_page value to be added", location="args"
)

event_download_parser = reqparse.RequestParser()
event_download_parser.add_argument(
    "start_date",
    type=inputs.datetime_from_iso8601,
    help="start datetime in ISO 8601 format like 2021-05-03T13:56:20",
    location="args",
)
event_download_parser.add_argument(
    "end_date",
    type=inputs.datetime_from_iso8601,
    help="end datetime in ISO 8601 format like 2021-05-03T13:56:20",
    location="args",
)
event_download_parser.add_argument(
    "robot_id", type=str, help="robot id to fetch logs for", location="args"
)

property_id_parser = reqparse.RequestParser()
property_id_parser.add_argument(
    "property_id", type=str, help="Property id of the property used", location="args"
)
