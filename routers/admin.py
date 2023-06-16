#admin can search for the particular user
#admin can able get the all students list
#admin can able to delete a user if he needs along with his details and tokens

from fastapi import Depends, APIRouter
from database import SessionLocal
import models
from sqlalchemy.orm import Session, Query
from starlette import status
from routers.auth import get_current_user


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={401: {'user':'Not Authorozed'}}
)

@router.get("/search/{username}")
async def search_by_username( username: str, user:dict = Depends(get_current_user), db:Session=Depends(get_db)):
    if user and user.get('is_admin'):
        searched_item =  db.query(models.StudentTable).filter(models.StudentTable.username == username).first()
        return  searched_item
    else:
        return "Authentication failed"
    
@router.get("/student_list", status_code=status.HTTP_200_OK)
async def list_of_students(db:Session=Depends(get_db), user:dict = Depends(get_current_user), page: int = 1, page_size:int = 10):
    if user and user.get('is_admin'):
        start_index = (page - 1) * page_size
        query: Query = db.query(models.StudentTable)
        paginated_items = query.offset(start_index).limit(page_size).all()
        return paginated_items
    return "Authentication failed"


@router.delete("/deleteUser/{username}", status_code=status.HTTP_200_OK)
async def delete_user(username: str,user:dict = Depends(get_current_user), db:Session=Depends(get_db)):
    if user and user.get('is_admin'):
        student = db.query(models.StudentTable).filter(models.StudentTable.username == username).first()
        if not student:
            return {"msg": "user not found"}
        
        contacts = db.query(models.PhoneBook).filter(models.PhoneBook.user_id == student.id).all()
        tokens = db.query(models.Token).filter(models.Token.student_id == student.id).all()
        for contact in contacts:
            db.delete(contact)
        for token in tokens:
            db.delete(token)
        db.delete(student)
        db.commit()
        return {"msg": "user and details are deleted"}

# @router.get("/filter_item", status_code=status.HTTP_200_OK)
# async def filter(address: str, user:dict = Depends(get_current_user), db:Session=Depends(get_db)):
#     if user is None or user.get('is_admin') == 'True':
#         return "user not found"
#     filtered_item = db.query(models.StudentTable).filter(models.StudentTable.address == address).all()
#     if filtered_item:
#         return filtered_item
#     return "not found"


    