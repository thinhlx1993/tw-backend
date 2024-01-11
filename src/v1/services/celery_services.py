"""Celery services"""
from src import db
from src.v1.models.celery import Celery


def add_celery_task(task_id, status, s3_url):
    """
    Add celery task details

    :param str task_id: celery task id
    :param str status: celery task status
    :param str s3_utl: s3 bucket url
    """

    try:
        new_celery_task = Celery(task_id, status, s3_url)
        db.session.add(new_celery_task)
        db.session.flush()
        return True, new_celery_task
    except Exception as err:
        db.session.rollback()
        raise Exception("Unable to add task in DB")


def update_celery_task(data: dict) -> (bool, dict):
    """
    update celery task details

    :param str data: dictionary containing data to be updated
    """
    try:
        status = data.get("status", None)
        s3_url = data.get("s3_url", None)
        task_details = Celery.query.filter(
            Celery.task_id == data.get("task_id", None)).first()
        if not task_details:
            raise Exception("Invalid Key")
        if status:
            task_details.status = status
        if s3_url:
            task_details.s3_url = s3_url
        # TODO:This needs to be flushed within request scope and committed
        # outside of request scope. Maybe somehow we check if we are inside
        # a request scope here
        db.session.flush()
        db.session.commit()
        return True, task_details
    
    except Exception as err:
        db.session.rollback()
        raise Exception("Unable to update task in DB")


def get_task_details(task_id):
    """
    Get celery task details

    :param str task_id: celery task id
    """

    try:
        task_details = Celery.query.filter(
            Celery.task_id == task_id).first()
        if not task_details:
            raise Exception("Task " + task_id +" is not present ")
        return task_details
    
    except Exception as err:
        db.session.rollback()
        raise Exception(err)
