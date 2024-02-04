"""Controller for posts."""
from flask_restx import fields, Resource
from flask_jwt_extended import get_jwt_claims

from src.parsers import page_parser, profile_page_parse
from src.services import post_services
from src.version_handler import api_version_1_web
from src.utilities.custom_decorator import custom_jwt_required

posts_ns = api_version_1_web.namespace("posts", description="Posts Functionalities")

post_model = posts_ns.model(
    "PostModel",
    {
        "title": fields.String(required=False, example="Post Title"),
        "content": fields.String(required=False, example="Post Content"),
        "like": fields.String(required=False, example="New Post Content"),
        "comment": fields.String(required=False, example="New Post Content"),
        "share": fields.String(required=False, example="New Post Content"),
        "view": fields.String(required=False, example="New Post Content"),
        "tw_post_id": fields.String(required=False, example="tw_post_id"),
        "profile_id": fields.String(required=True, example="profile_id"),
        "post_date": fields.String(required=True, example="post_date"),
        "username": fields.String(required=False, example="username"),
        "is_deleted": fields.Boolean(example=True, required=False),
    },
)

post_update_model = posts_ns.model(
    "PostUpdateModel",
    {
        "title": fields.String(example="New Post Title"),
        "content": fields.String(example="New Post Content"),
        "like": fields.String(example="New Post Content"),
        "comment": fields.String(example="New Post Content"),
        "share": fields.String(example="New Post Content"),
        "view": fields.String(example="New Post Content"),
        "post_date": fields.String(example="New Post date content"),
        "is_deleted": fields.Boolean(example=True, required=False),
    },
)


class PostsController(Resource):
    """Class for /posts functionalities."""

    @posts_ns.expect(profile_page_parse)
    @posts_ns.response(200, "Success")
    @custom_jwt_required()
    def get(self):
        """Retrieve list of posts"""
        args = profile_page_parse.parse_args()
        page = args.get("page", 1)
        per_page = args.get("per_page", 20)
        sort_by = args.get("sort_by", "created_at")
        sort_order = args.get("sort_order", "desc")
        search = args.get("search", "")
        profile_id = args.get("profile_id", "")
        posts = post_services.get_all_posts(
            page, per_page, sort_by, sort_order, search, profile_id
        )
        return posts, 200

    @posts_ns.expect(post_model)
    @posts_ns.response(201, "Post created")
    @custom_jwt_required()
    def post(self):
        """Create a new post"""
        data = posts_ns.payload
        claims = get_jwt_claims()
        data["crawl_by"] = claims["user_id"]
        tw_post_id = data.get("tw_post_id", None)
        post = post_services.create_or_update_post(
            tw_post_id=tw_post_id, post_data=data
        )
        return post.repr_name(), 201


class PostIdController(Resource):
    """Class for /posts/<post_id> functionalities."""

    @posts_ns.response(200, "Success")
    @posts_ns.response(404, "Post not found")
    @custom_jwt_required()
    def get(self, tw_post_id):
        """Retrieve a specific post by ID"""
        post = post_services.get_post_by_id(tw_post_id)
        if post:
            return post.repr_name(), 200
        else:
            return {"message": "Post not found"}, 404

    @posts_ns.expect(post_update_model)
    @posts_ns.response(200, "Post updated")
    @posts_ns.response(404, "Post not found")
    @custom_jwt_required()
    def put(self, tw_post_id):
        """Update a post by ID"""
        data = posts_ns.payload
        success = post_services.create_or_update_post(tw_post_id, data)
        if success:
            return {"message": "Post updated"}, 200
        else:
            return {"message": "Post not found"}, 404

    @posts_ns.response(200, "Post deleted")
    @posts_ns.response(404, "Post not found")
    @custom_jwt_required()
    def delete(self, tw_post_id):
        """Delete a post by ID"""
        success = post_services.delete_post(tw_post_id)
        if success:
            return {"message": "Post deleted"}, 200
        else:
            return {"message": "Post not found"}, 404


# Registering the resources
posts_ns.add_resource(PostsController, "/")
posts_ns.add_resource(PostIdController, "/<string:tw_post_id>")
