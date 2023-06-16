from fastapi import Depends, HTTPException, status
from sqlalchemy import and_
import models
from pydantic import BaseModel, validator, Field
from database import SessionLocal
from sqlalchemy.orm import Session, Query
from fastapi import APIRouter
from routers.users import get_current_user
import re

router = APIRouter(
    prefix="/contact",
    tags=["contacts"],
    responses={401: {'user':'Not Authorozed'}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

#basemodel to add contact
class AddContacts(BaseModel):
    name: str = Field(..., min_length=4)
    phonenumber: str
    
    @validator('phonenumber')
    def validate_phone_number(cls, value):
        pattern = r'^\+91[1-9]\d{9}$'
        if not re.match(pattern, value):
            raise ValueError('Invalid Indian mobile number format')
        return value


#api to get the contacts of a user who is loged in
@router.get("/my_contacts", status_code=status.HTTP_200_OK)
async def myContacts(user: dict = Depends(get_current_user), db: Session=Depends(get_db), page: int = 1, page_size:int = 5):
    if user:  
        start_index = (page - 1) * page_size
        query: Query = db.query(models.PhoneBook)
        paginated_items = query.offset(start_index).limit(page_size).all()
        return paginated_items
    raise get_user_exception()
    

#api to add contact 
@router.post("/add_contacts", status_code=status.HTTP_201_CREATED)
async def add_contacts(add_contact : AddContacts, user: dict = Depends(get_current_user), db: Session=Depends(get_db)):
    
    if user is None:
        raise get_user_exception()
    contacts = models.PhoneBook()
    contacts.name = add_contact.name
    contacts.phonenumber = add_contact.phonenumber
    contacts.user_id = user.get("id")

    #checks the name of a contact is already stored in a database for a specific user
    check_user = db.query(models.PhoneBook).filter(and_(models.PhoneBook.name == add_contact.name,models.PhoneBook.user_id == user.get("id"))).first()
    if check_user:
        return {"msg": "username already exist"}
    else: 
        db.add(contacts)
        db.commit()
    return {"msg": "Contact Added"}


#api to edit a users contact
@router.put("/edit_contacts/{id}", status_code=status.HTTP_205_RESET_CONTENT)
async def edit_contacts(id: int,edit_contact: AddContacts, user: dict = Depends(get_current_user), db: Session=Depends(get_db)):
    if user is None:
        raise get_user_exception()
    contact = db.query(models.PhoneBook)\
        .filter(models.PhoneBook.id == id)\
        .filter(models.PhoneBook.user_id == user.get("id"))\
        .first()

    if contact is None:
        raise HTTPException(status_code=404, detail="not Found")
    
    contact.name = edit_contact.name
    contact.phonenumber = edit_contact.phonenumber

    db.add(contact)
    db.commit()
    return {"msg" : "Successfully edited"}


#api to delete a user contact
@router.delete("/delete_contacts/{id}",status_code=status.HTTP_200_OK)
async def delete_contacts(id: int, user:dict = Depends(get_current_user), db: Session=Depends(get_db)):
    if user is None:
        raise get_user_exception()
    contact = db.query(models.PhoneBook).filter(models.PhoneBook.id == id).filter(models.PhoneBook.user_id == user.get("id")).delete()
    if contact:
        db.commit()
    else:
        return "contact not found"
    return {"msg": "Successfully Deleted"}


def get_user_exception():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return credentials_exception
