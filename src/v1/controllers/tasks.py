from flask_restx import Resource, fields
from src.services import tasks_services
from src.version_handler import api_version_1_web

# from src.services import tasks_services
from src.utilities.custom_decorator import custom_jwt_required

tasks_ns = api_version_1_web.namespace("tasks", description="Tasks Functionalities")

# Task model for creation
task_create_model = tasks_ns.model(
    "TaskCreateModel",
    {
        "tasks_name": fields.String(required=True, example="Task Name"),
        "tasks_json": fields.Raw(
            required=False, example={"key": "value"}, description="JSON for task"
        ),
    },
)

# Task model for update
task_update_model = tasks_ns.model(
    "TaskUpdateModel",
    {
        "tasks_name": fields.String(required=False, example="New Task Name"),
        "tasks_json": fields.Raw(
            required=False,
            example={"new_key": "new_value"},
            description="Updated JSON for task",
        ),
    },
)

# Task response model
task_response_model = tasks_ns.model(
    "TaskResponseModel",
    {
        "message": fields.String(example="Operation successful"),
        "task": fields.Nested(task_create_model, description="Task details"),
    },
)


class TasksController(Resource):
    """Controller for tasks functionalities."""

    @tasks_ns.expect()
    @tasks_ns.response(200, "OK", task_response_model)
    @tasks_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def get(self):
        """Retrieve a list of tasks."""
        try:
            tasks = tasks_services.get_all_tasks()
            return {"message": "Tasks fetched successfully", "tasks": tasks}, 200
        except Exception as e:
            return {"message": str(e)}, 500

    @tasks_ns.expect(task_create_model)
    @tasks_ns.response(201, "Task Created", task_response_model)
    @tasks_ns.response(400, "Bad Request")
    @tasks_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def post(self):
        """Create a new task."""
        data = tasks_ns.payload
        task = tasks_services.create_task(data)
        return {"message": "Task created successfully", "task": task}, 201


class TaskIdController(Resource):
    """Controller for specific task functionalities."""

    @tasks_ns.expect(task_update_model)
    @tasks_ns.response(200, "Task Updated", task_response_model)
    @tasks_ns.response(400, "Bad Request")
    @tasks_ns.response(404, "Not Found")
    @tasks_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def put(self, task_id):
        """Update a specific task."""
        try:
            data = tasks_ns.payload
            task = tasks_services.update_task(task_id, data)
            if not task:
                return {"message": "Task not found"}, 404
            return {"message": "Task updated successfully", "task": task}, 200
        except Exception as e:
            return {"message": str(e)}, 500

    @tasks_ns.response(200, "Task Deleted", task_response_model)
    @tasks_ns.response(404, "Not Found")
    @tasks_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def delete(self, task_id):
        """Delete a specific task."""
        try:
            result = tasks_services.delete_task(task_id)
            if result:
                return {"message": "Task deleted successfully"}, 200
            return {"message": "Task not found"}, 404
        except Exception as e:
            return {"message": str(e)}, 500


# Add resources to namespace
tasks_ns.add_resource(TasksController, "/")
tasks_ns.add_resource(TaskIdController, "/<string:task_id>")
