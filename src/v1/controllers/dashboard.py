from flask_restx import Resource

from src import cache
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web
from src.services import dashboard_services  # You need to create this

# Create a new namespace for the dashboard
dashboard_ns = api_version_1_web.namespace(
    "dashboard", description="Dashboard functionalities"
)


# Dashboard Controller
class DashboardController(Resource):
    @dashboard_ns.response(200, "Success")
    @custom_jwt_required()  # or @custom_jwt_required() if you have a custom JWT decorator
    @cache.cached(timeout=3600)
    def get(self):
        """Retrieve dashboard data"""
        # Fetch data for the dashboard using a service
        data = dashboard_services.get_dashboard_data()
        return data, 200


# Registering the resource
dashboard_ns.add_resource(DashboardController, "/")
