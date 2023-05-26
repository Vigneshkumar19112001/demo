from fastapi import  Depends, HTTPException, Request, Response, APIRouter
import models
from database import SessionLocal
from pydantic import BaseModel, validator, Field, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime
from starlette import status
from datetime import date


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {'user': "Not authorized"}}
)

SECRET_KEY = "fb5547d9094d960a71a6d4be312b6a3fd50dea49cf47fd8d77b817b520396375"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')
PASSWORD = "Nothing"


class StudentLogin(BaseModel):
    username : str = Field(...,min_length=4)
    password : str = Field(...,min_length=8)
    email : EmailStr
    first_name : str
    last_name : str
    reg_no : str
    phonenumber : str
    address : str
    gender : str
    dob : date
    is_admin : bool = False
    pwd: str = None
    

    @validator('username')
    def username_validation(cls, v):
        assert v.isalnum(), 'must be an alphanumeric'
        return v
    
    @validator('reg_no')
    def validate_reg_no(cls, value):
        if value == 0:
            raise ValueError("reg_no should be greater then 0")
        return value
    
    @validator('gender')
    def gender_validation(cls, value):
        if value not in ('male', 'female', 'others'):
            raise ValueError("gender must be male, female or others")
        return value
    
    @validator('password')
    def password_validator(cls, value):
        assert value.isalnum(), 'must be an alphanumeric'
        return value
    


class Token(BaseModel):
    refresh_token: str
    access_token: str
    token_type: str

class Login(BaseModel):
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


def hash_passord(pwd):
    return bcrypt_context.hash(pwd)

def check_password(password, pwd):
    return bcrypt_context.verify(password, pwd)

def authenticate_user(username: str, pwd: str, db):
    user = db.query(models.StudentTable).filter(models.StudentTable.username == username).first() or db.query(models.StudentTable).filter(models.StudentTable.email == username).first()
    if not user:
        return False
    if not check_password(pwd, user.password):
        return False
    return user

def create_access_token(username: str, user_id: int, is_admin: bool, expiretime):
    encode = {'sub': username, 'id': user_id, 'is_admin': is_admin}
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(username: str, user_id: int, is_admin: bool, expiretime):
    refresh_token = {'sub': username, 'id': user_id, 'is_admin': is_admin}
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token.update({'exp': expires})
    return jwt.encode(refresh_token, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str=Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
    

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: bool = payload.get('is_admin')
        if username is None or user_id is None or is_admin is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate user")
        return {'username': username, 'id': user_id, 'is_admin': is_admin}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate user")
    

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_student(student : StudentLogin, db: Session = Depends(get_db)):
    new_student = models.StudentTable()

    new_student.username = student.username
    new_student.password = hash_passord(student.password)
    new_student.email = student.email
    new_student.first_name = student.first_name
    new_student.last_name = student.last_name
    new_student.reg_no =  student.reg_no
    new_student.phone_number = student.phonenumber
    new_student.address = student.address
    new_student.gender = student.gender
    new_student.dob = student.dob
    new_student.is_admin = student.is_admin

    check_user = db.query(models.StudentTable).filter(models.StudentTable.username == student.username).first()
    check_email = db.query(models.StudentTable).filter(models.StudentTable.email == student.email).first()
    check_reg_no = db.query(models.StudentTable).filter(models.StudentTable.reg_no == student.reg_no).first()

    if check_user:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="User Already Existed")
    elif check_email:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="Email Already Existes")
    elif check_reg_no:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="reg_no Already Existes")
    elif student.is_admin:
        if student.pwd != PASSWORD:
            return {"error": "Incorrect Password"}
        else:
            db.add(new_student)
            db.commit()
            return {"message": "admin Login Successful"}    
    else:
        db.add(new_student)
        db.commit()
    return {"message": "Student Login Successful"}


@router.post("/login", response_model=Token, status_code=status.HTTP_201_CREATED)
async def login_for_access_token(response: Response, form: Login, db:Session=Depends(get_db)):
    user = authenticate_user(form.username, form.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate user")
    access_token = create_access_token(user.username, user.id, user.is_admin,timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(user.username, user.id, user.is_admin,timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {'refresh_token': refresh_token, 'access_token': access_token, 'token_type': 'bearer'}
    

@router.get("/refresh_token", status_code=status.HTTP_200_OK)
async def refresh_token(request: Request, user: dict = Depends(get_current_user), db:Session=Depends(get_db)):

    # url = "http://127.0.0.1:8000/refresh_token"
    token = request.cookies['refresh_token']
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = user.get('id')
    username = user.get('sub')
    is_admin = user.get('is_admin')
    new_access_token = create_access_token(user_id, username, is_admin, timedelta(minutes=REFRESH_TOKEN_EXPIRE_DAYS))

    return {"new_access_token": new_access_token}


@router.get("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie(key='access_token')
    response.delete_cookie(key='refresh_token')
    return "Logout Successfull"
