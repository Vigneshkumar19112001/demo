from fastapi import Depends, HTTPException, Request, APIRouter
import models
from database import SessionLocal
from pydantic import BaseModel, validator, Field, EmailStr
from sqlalchemy.orm import Session
from datetime import date
from starlette import status
from routers.auth import check_password, hash_passord, get_current_user


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={401: {'user': "Not authorized"}}
)
    

class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str

    @validator('username')
    def username_validation(cls, v):
        assert v.isalnum(), 'must be an alphanumeric'
        return v

    @validator('password')
    def password_validator(cls, value):
        assert value.isalnum(), 'must be an alphanumeric'
        return value


class ForgetPassword(BaseModel):
    username: str = Field(...,min_length=4)
    password: str = Field(...,min_length=8)

    @validator('username')
    def username_validation(cls, v):
        assert v.isalnum(), 'must be an alphanumeric'
        return v

    @validator('password')
    def password_validator(cls, value):
        assert value.isalnum(), 'must be an alphanumeric'
        return value


@router.put("/forget_password", status_code=status.HTTP_205_RESET_CONTENT)
def forget_password(forget_password: ForgetPassword, db:Session=Depends(get_db)):
    user = db.query(models.StudentTable).filter(models.StudentTable.email == forget_password.username).first() or db.query(models.StudentTable).filter(models.StudentTable.username == forget_password.username).first()

    if user is not None:
        user.password = hash_passord(forget_password.password)
        
        db.add(user)
        db.commit()
        return "Successfully changed"
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="userName or email not found")


@router.post("/edit_password", status_code=status.HTTP_205_RESET_CONTENT)
async def edit_password(request: Request, user_verification: UserVerification, user: dict = Depends(get_current_user), db: Session=Depends(get_db)):
    if user is None:
        return "user not found"
    student_model = db.query(models.StudentTable).filter(models.StudentTable.id == user.get('id')).first()

    if student_model is not None:
        if user_verification.username == student_model.username and check_password(user_verification.password,student_model.password):
            student_model.password = hash_passord(user_verification.new_password)
            db.add(student_model)
            db.commit()
            return 'Successful'
    return 'Invalid user or request'

