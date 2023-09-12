from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, update

from Database import models
from Database.sql import engine, SessionLocal
# from Database.schema import CabBase, CabsResponse, DriversResponse, DriverBase, DeleteResponse, SearchRequest

# from Database.validation import validateDriver, validateCab, validateEmail

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Paper Crypto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/users/{uid}", tags=["User"])
def get_user(uid: str,  db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.uid == uid).first()

    return user

@app.get("/get_users", tags=["Admin"])
def get_user(db: Session = Depends(get_db)):
    users = db.query(models.User).all()

    return users

@app.post("/create_user", tags=["User"])
def create_user(uid: str, First_Name:str, Last_Name: str, Email: str, Phone: str,  db: Session = Depends(get_db)):
    user_object = models.User(uid = uid, First_Name=First_Name, Last_Name = Last_Name, Email = Email)

    if(Phone):
        user_object.Phone = Phone

    user_object.Current_Balance = 0

    user_object.Account_Status = 1

    try:
        db.add(user_object)
        db.commit()
    except SQLAlchemyError as e:
        print("Error creating user:", str(e))
        raise HTTPException(status_code=500, detail="Error creating user")

    return user_object

@app.post("/add_balance", tags=["User"])
def create_user(uid: str, amount : str,  db: Session = Depends(get_db)):
    
    user_obj = db.query(models.User).filter_by(uid=uid).first()

    user_obj.Current_Balance += int(amount)

    transaction = models.AccountTransactions(user_id = uid, transaction_type = "Deposit", amount=amount)

    try:
        db.add(transaction)
        db.commit()
    except SQLAlchemyError as e:
        print("Error during deposit:", str(e))
        raise HTTPException(status_code=500, detail="Error during deposit")

    return {"status": "Success"}

@app.post("/withdraw_money", tags=["User"])
def create_user(uid: str, amount : str,  db: Session = Depends(get_db)):
    
    user_obj = db.query(models.User).filter_by(uid=uid).first()

    if(user_obj.Current_Balance >= int(amount)):
        user_obj.Current_Balance -= int(amount)
    else:
        return {"status" : "Failure", "message" : "Not enough funds to withdraw"}

    transaction = models.AccountTransactions(user_id = uid, transaction_type = "Withdrawal", amount=amount)

    try:
        db.add(transaction)
        db.commit()
    except SQLAlchemyError as e:
        print("Error during withdrawal:", str(e))
        raise HTTPException(status_code=500, detail="Error during withdrawal")

    return {"status": "Success"}

@app.get("/users/{uid}/fetch_balance", tags=["User"])
def get_user(uid: str,  db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.uid == uid).first()

    if user:
        return {"user_id": uid, "balance": user.Current_Balance}
    else:
        raise HTTPException(status_code=404, detail=f"User with ID {uid} not found")