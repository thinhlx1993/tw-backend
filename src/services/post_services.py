import math

from sqlalchemy import or_

from src import db, app
from src.models.posts import Posts  # Importing the Posts model


def get_post_by_id(tw_post_id):
    """Retrieve a post by its ID."""
    post_record = Posts.query.filter_by(tw_post_id=tw_post_id).first()
    return post_record


def get_all_posts(
    page=0,
    per_page=20,
    sort_by="created_at",
    sort_order="desc",
    search="",
    profile_id="",
    user_id="",
):
    column = getattr(Posts, sort_by, None)
    if not column:
        return False, {"Message": "Invalid sort_by key provided"}
    sorting_order = sort_by + " " + sort_order
    query = Posts.query.filter(Posts.is_deleted == False)
    # Apply sorting
    if sorting_order:
        query = query.order_by(db.text(sorting_order))
    if search:
        query = query.filter(
            or_(
                Posts.title.ilike(f"%{search}%"),
                Posts.username.ilike(f"%{search}%"),
                Posts.content.ilike(f"%{search}%"),
                Posts.tw_post_id.ilike(f"%{search}%"),
            )
        )
    if profile_id:
        query = query.filter(Posts.profile_id == profile_id)
    if user_id:
        query = query.filter(Posts.crawl_by == user_id)

    query = query.execution_options(bind=db.get_engine(app, bind='readonly'))
    # Apply pagination
    count = query.count()

    if per_page:
        query = query.limit(per_page)
    if page:
        query = query.offset(per_page * (page - 1))
    posts = query.all()
    # Formatting the result
    formatted_result = [post.repr_name() for post in posts]
    return {
        "data": formatted_result,
        "result_count": count,
        "max_pages": math.ceil(count / per_page),
    }


def create_or_update_post(tw_post_id, post_data):
    """Create or update a post."""
    post_record = Posts.query.filter_by(tw_post_id=tw_post_id).first()

    if post_record:
        # Update existing record with new data
        for key, value in post_data.items():
            setattr(post_record, key, value)
    else:
        # Create a new record
        post_record = Posts()
        post_record.is_deleted = False
        for key, val in post_data.items():
            if hasattr(post_record, key):
                post_record.__setattr__(key, val)
        db.session.add(post_record)

    db.session.flush()
    return post_record


def delete_post(tw_post_id):
    """Delete a post by its ID."""
    post_record = Posts.query.filter_by(tw_post_id=tw_post_id).first()
    if post_record:
        db.session.delete(post_record)
        db.session.flush()
        return True
    return False
