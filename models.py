from sqlalchemy import String, Integer, Column, DATE, Boolean
from database import Base

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

