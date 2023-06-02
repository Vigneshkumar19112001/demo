# 1.store refresh token and access token
# 2.for multiple login use multiple refresh and access token
# 3.access token has to refresh for every time when the acces token expires
# 4.for generating access token first check whether the refresh token is expired or not
# 5.delete the refresh token once expires

from typing import Optional
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
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

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

def create_access_token(username: str, user_id: int, is_admin: bool, expiretime: Optional[timedelta] = None):
    encode = {'sub': username, 'id': user_id, 'is_admin': is_admin}
    if expiretime:
        expire = datetime.utcnow() + expiretime
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

refresh_expire_at = datetime.utcnow() + timedelta(REFRESH_TOKEN_EXPIRE_DAYS)

def create_refresh_token(username: str, user_id: int, is_admin: bool, expiretime):
    refresh_token = {'sub': username, 'id': user_id, 'is_admin': is_admin}
    if expiretime:
        expire = datetime.utcnow() + expiretime
    else:
        expire = datetime.utcnow() + refresh_expire_at
    refresh_token.update({'exp': expire})
    return jwt.encode(refresh_token, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(db:Session, token:str):
    try:
        refresh_token = db.query(models.Token).filter(models.Token.tokens == token).first()
        if refresh_token and refresh_token.expire_at > datetime.now():
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        else:
            return {'msg' : 'Authentication Failed'}
    except jwt.JWTError:
        return None


def update_access_token(refresh_token: str, new_access_token: str, db: Session):
    token = db.query(models.Token).filter(models.Token.tokens == refresh_token).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    token.access_token = new_access_token
    db.commit()
    return {'msg' : 'Token added to the database'}
    
# def store_refresh_token(db: Session, student_id: int, token: str):
#     refresh_token = models.Token(tokens=token, student_id=student_id)
#     db.add(refresh_token)
#     db.commit()
#     db.refresh(refresh_token)
#     return refresh_token

def save_refresh_token(db: Session, student_id: int, refresh_token: str, access:str, expire_at: datetime):
    new_refresh_token = models.Token(tokens=refresh_token, student_id=student_id, access_token=access, expire_at = expire_at)
    db.add(new_refresh_token)
    db.commit()
    return "token created"

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
    access_token = create_access_token(user.username, user.id, user.is_admin, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(user.username, user.id, user.is_admin, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    save_refresh_token(db,user.id,refresh_token,access_token, refresh_expire_at)
    response.set_cookie(key="access_token", value=access_token, httponly=True) #to be deleted
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True) #to be deleted
    return {'refresh_token': refresh_token, 'access_token': access_token, 'token_type': 'bearer'}

@router.get("/token")
async def get_all_token(db: Session=Depends(get_db)):
    return db.query(models.Token).all()

@router.delete("/delete_token/{student_id}")
async def delete_token(student_id :int, db: Session=Depends(get_db)):
    delete_id =  db.query(models.Token).filter(models.Token.token_id == student_id).delete()
    if delete_id:
        db.commit()
        return "user deleted"
    return "user not found"


@router.get("/refresh_token", status_code=status.HTTP_200_OK)
async def refresh_token(request: Request, user: dict = Depends(get_current_user), db:Session=Depends(get_db)):
    token = request.cookies['refresh_token']
    if verify_token(db, token):
        user_id = user.get('id')
        username = user.get('sub')
        is_admin = user.get('is_admin')
        new_access_token = create_access_token(user_id, username, is_admin, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        update_access_token(token, new_access_token, db)
        return {"new_access_token": new_access_token}
    return {"new_access_token": ""}


@router.get("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie(key='access_token')
    response.delete_cookie(key='refresh_token')
    return "Logout Successfull"
