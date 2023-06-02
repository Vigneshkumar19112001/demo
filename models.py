from sqlalchemy import String, Integer, Column, DATE, Boolean, ForeignKey, BOOLEAN, DateTime
from database import Base
from sqlalchemy.orm import relationship

class StudentTable(Base):
    __tablename__ = "student_login"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    reg_no = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False)
    address = Column(String, nullable=True)
    gender = Column(String, nullable=False)
    dob = Column(DATE)
    is_admin = Column(Boolean, default="False")

    refresh_tokens = relationship('Token', back_populates='login_token')


class Token(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(Integer, primary_key=True, index=True)
    tokens = Column(String, nullable=False)
    student_id = Column(Integer, ForeignKey("student_login.id"),nullable=False)
    access_token = Column(String, nullable=False)
    expire_at = Column(DateTime, nullable=False)

    login_token = relationship('StudentTable', back_populates='refresh_tokens')

