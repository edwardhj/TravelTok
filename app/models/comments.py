from .db import db, environment, SCHEMA, add_prefix_for_prod
from datetime import datetime
from sqlalchemy.orm import relationship

class Comment(db.Model):
    __tablename__ = 'comments'

    if environment == "production":
        __table_args__ = {'schema': SCHEMA}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('users.id'), ondelete='CASCADE'), nullable=False)
    clip_id = db.Column(db.Integer, db.ForeignKey(add_prefix_for_prod('clips.id'), ondelete='CASCADE'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    poster = relationship('User', back_populates='posted_comments')
    clip_comment = relationship('Clip', back_populates='comments_on_clip')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'clip_id': self.clip_id,
            'body': self.body,
            'creator': self.poster.username
        }
