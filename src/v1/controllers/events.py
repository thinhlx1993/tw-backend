"""Controller for events."""
from flask_jwt_extended import get_jwt_claims
from flask_restx import fields, Resource

from src.parsers import page_parser, event_page_parser
from src.services import events_services  # Import your events services
from src.version_handler import api_version_1_web
from src.utilities.custom_decorator import custom_jwt_required

events_ns = api_version_1_web.namespace("events", description="Events Functionalities")

event_model = events_ns.model(
    "EventModel",
    {
        "issue": fields.String(required=False, example="issue"),
        "event_type": fields.String(required=True, example="event_type"),
        "profile_id": fields.String(required=False, example="profile_id"),
        "profile_id_interact": fields.String(required=False, example="profile_id"),
        "schedule_id": fields.String(required=False, example="event_id"),
        "mission_id": fields.String(required=False, example="mission_id"),
    },
)

event_update_model = events_ns.model(
    "EventUpdateModel",
    {
        "issue": fields.String(example="issue")
        # Add other fields for update as per your Events model
    },
)


class EventsController(Resource):
    """Class for /events functionalities."""

    @events_ns.expect(event_page_parser)
    @events_ns.response(200, "Success")
    @custom_jwt_required()
    def get(self):
        """Retrieve list of events"""
        args = event_page_parser.parse_args()
        # Pagination settings
        page = args.get("page", 1) if args.get("page") else None
        per_page = args.get("per_page") if args.get("per_page") else None
        # Sorts by 'teams_name' by default
        sort_by = str(args.get("sort_by")) if args.get("sort_by") else "created_at"
        # Sorts ascending by default
        sort_order = str(args.get("sort_order")) if args.get("sort_order") else "desc"
        if sort_order.lower() not in ["asc", "desc"]:
            return {"message": "Invalid sort order"}, 400
        # Read any filters specified
        search = args.get("search", "").strip().lower()
        receiver = args.get("receiver", "").strip().lower()
        giver = args.get("giver", "").strip().lower()
        events = events_services.get_all_events(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            receiver_username=receiver,
            giver_username=giver,
        )
        return events, 200

    @events_ns.expect(event_model)
    @events_ns.response(201, "Event created")
    @custom_jwt_required()
    def post(self):
        """Create a new event"""
        data = events_ns.payload
        event = events_services.create_or_update_event(event_id=None, event_data=data)
        return event.repr_name(), 201


class EventIdController(Resource):
    """Class for /events/<event_id> functionalities."""

    @events_ns.response(200, "Success")
    @events_ns.response(404, "Event not found")
    @custom_jwt_required()
    def get(self, event_id):
        """Retrieve a specific event by ID"""
        event = events_services.get_event_by_id(event_id)
        if event:
            return event.repr_name(), 200
        return {"message": "Event not found"}, 404

    @events_ns.expect(event_update_model)
    @events_ns.response(200, "Event updated")
    @events_ns.response(404, "Event not found")
    @custom_jwt_required()
    def put(self, event_id):
        """Update an event by ID"""
        data = events_ns.payload
        success = events_services.create_or_update_event(event_id, data)
        if success:
            return {"message": "Event updated"}, 200
        else:
            return {"message": "Event not found"}, 404

    @events_ns.response(200, "Event deleted")
    @events_ns.response(404, "Event not found")
    @custom_jwt_required()
    def delete(self, event_id):
        """Delete an event by ID"""
        success = events_services.delete_event(event_id)
        if success:
            return {"message": "Event deleted"}, 200
        else:
            return {"message": "Event not found"}, 404


# Registering the resources
events_ns.add_resource(EventsController, "/")
events_ns.add_resource(EventIdController, "/<string:event_id>")
