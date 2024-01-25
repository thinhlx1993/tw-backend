from src import db
from sqlalchemy import text, ForeignKey, func
from sqlalchemy.orm import relationship


class Posts(db.Model):
    """
    Model for blog posts or similar content
    """

    __tablename__ = "posts"

    post_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True
    )
    title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text(), nullable=True)
    tw_post_id = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(
        db.String(128), ForeignKey("profiles.profile_id"), nullable=False
    )
    crawl_by = db.Column(db.String(128), ForeignKey("user.user_id"), nullable=True)
    created_at = db.Column(db.DateTime(), server_default=func.now())
    like = db.Column(db.String(128), nullable=True)
    comment = db.Column(db.String(128), nullable=True)
    share = db.Column(db.String(128), nullable=True)
    view = db.Column(db.String(128), nullable=True)
    post_date = db.Column(db.String(128), nullable=True)
    # Relationships
    profile = relationship("Profiles", foreign_keys=[profile_id])
    user = relationship("User", foreign_keys=[crawl_by])

    def repr_name(self):
        return {
            "post_id": self.post_id,
            "title": self.title,
            "content": self.content,
            "like": self.content,
            "comment": self.content,
            "share": self.content,
            "view": self.content,
            "tw_post_id": self.tw_post_id,
            "profile_crawl": self.profile.username if self.profile else None,
            "user_crawl": self.user.username if self.user else None,
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M"),
        }
