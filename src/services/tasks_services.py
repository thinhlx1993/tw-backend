from src import db, app
from src.models import Task


def get_all_tasks():
    """Retrieve all tasks."""
    task_names = ["Check follow", "newsFeed", "Login", "Lấy cookie", "reUpPost"]
    tasks = Task.query.filter(Task.tasks_name.in_(task_names)).all()
    tasks = [task.repr_name() for task in tasks]
    return tasks


def create_task(data):
    """Create a new task."""
    new_task = Task(
        tasks_name=data["tasks_name"], tasks_json=data.get("tasks_json", {})
    )
    db.session.add(new_task)
    db.session.commit()
    return new_task


def update_task(task_id, data):
    """Update an existing task."""
    task = Task.query.filter_by(tasks_id=task_id).first()
    if task:
        task.tasks_name = data.get("tasks_name", task.tasks_name)
        task.tasks_json = data.get("tasks_json", task.tasks_json)
        db.session.commit()
    return task


def delete_task(task_id):
    """Delete a task."""
    task = Task.query.filter_by(tasks_id=task_id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
        return True
    return False
