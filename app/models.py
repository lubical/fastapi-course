from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean, text

from .database import Base

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False) 
    published = Column(Boolean, server_default='TRUE')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    def __str__(self) -> str:
        return f"id {self.id} title {self.title} content {self.content}"