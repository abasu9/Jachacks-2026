import uuid
from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name = Column(String(255), nullable=False)
    apr = Column(ARRAY(Float), nullable=False)
    pip = Column(Integer, nullable=False)
    joiningDate = Column(Date, nullable=False)
    rank = Column(Float, nullable=False)
