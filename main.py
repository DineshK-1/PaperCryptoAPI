from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, update

from Database import models
from Database.sql import engine, SessionLocal

import httpx
# from Database.schema import CabBase, CabsResponse, DriversResponse, DriverBase, DeleteResponse, SearchRequest

# from Database.validation import validateDriver, validateCab, validateEmail

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Paper Crypto API")

origins = [
    "https://papercrypto.vercel.app",
    "http://localhost:8000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
def get_users(db: Session = Depends(get_db)):
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
def add_balance(uid: str, amount : str,  db: Session = Depends(get_db)):
    
    user_obj = db.query(models.User).filter_by(uid=uid).first()

    user_obj.Current_Balance += float(amount)

    transaction = models.AccountTransactions(user_id = uid, transaction_type = "Deposit", amount=amount)

    try:
        db.add(transaction)
        db.commit()
    except SQLAlchemyError as e:
        print("Error during deposit:", str(e))
        raise HTTPException(status_code=500, detail="Error during deposit")

    return {"status": "Success"}

@app.post("/withdraw_money", tags=["User"])
def withdraw_money(uid: str, amount : str,  db: Session = Depends(get_db)):
    
    user_obj = db.query(models.User).filter_by(uid=uid).first()

    if(user_obj.Current_Balance >= float(amount)):
        user_obj.Current_Balance -= float(amount)
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
    
@app.post("/users/{uid}/buy_crypto", tags=["Crypto"])
async def buy_crypto(uid : str, token_id : str, amount : float,  db: Session = Depends(get_db)):
    fetch_coin_data = f"https://coinranking1.p.rapidapi.com/coin/{token_id}"

    headers = {
        "X-RapidAPI-Key": "6c15ef80a9msh0fab964ed355602p120ff5jsn278d01eb24fb",
        "X-RapidAPI-Host": "coinranking1.p.rapidapi.com", 
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(fetch_coin_data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        data = data["data"]["coin"]
    else:
        return {"status": "Failed"}
    
    fiat_price = float(data["price"])*amount

    user_obj = db.query(models.User).filter(models.User.uid == uid).first()
    if user_obj.Current_Balance < fiat_price:
        return {"status": "Failed", "Reason" : "Not enough balance in the account"}


    user_obj.Current_Balance -= fiat_price
    
    user_holdings = db.query(models.CryptoHoldings).filter(models.CryptoHoldings.user_id == uid).filter(models.CryptoHoldings.token_id == token_id).first()

    if user_holdings is None:
        holding_obj = models.CryptoHoldings(user_id = uid, token_id = token_id, token_name=data["name"], token_symbol=data["symbol"], amount=amount)
    else:
        holding_obj = user_holdings
        holding_obj.amount += amount

    transaction = models.CryptoTransactions(user_id = uid, transaction_type = "BUY", token_id=token_id, token_name=data["name"], token_symbol=data["symbol"], token_price = data["price"], amount=amount)

    try:
        db.add(holding_obj)
        db.add(transaction)
        db.commit()
    except SQLAlchemyError as e:
        print("Error during purchasing:", str(e))
        raise HTTPException(status_code=404, detail="Error during purchasing")
    
    return {"status" : "Success"}

@app.post("/users/{uid}/sell_crypto", tags=["Crypto"])
async def sell_crypto(uid : str, token_id : str, amount : float,  db: Session = Depends(get_db)):
    fetch_coin_data = f"https://coinranking1.p.rapidapi.com/coin/{token_id}"

    headers = {
        "X-RapidAPI-Key": "6c15ef80a9msh0fab964ed355602p120ff5jsn278d01eb24fb",
        "X-RapidAPI-Host": "coinranking1.p.rapidapi.com", 
    }

    user_holding = db.query(models.CryptoHoldings).filter(models.CryptoHoldings.user_id == uid).filter(models.CryptoHoldings.token_id == token_id).first()
    
    holding_amount = 0

    for holding in user_holding:
        holding_amount += holding.amount

    if holding_amount >= amount:
        user_holding.amount -= amount
        async with httpx.AsyncClient() as client:
            response = await client.get(fetch_coin_data, headers=headers)

        if response.status_code == 200:
            data = response.json()
            data = data["data"]["coin"]
        else:
            return {"status": "Failed"}
        
        transaction = models.CryptoTransactions(user_id = uid, transaction_type = "SELL", token_id=token_id, token_name=data["name"], token_symbol=data["symbol"], token_price = data["price"], amount=amount)
        user_obj = db.query(models.User).filter(models.User.uid == uid).first()

        fiat_cash = float(data["price"])*amount

        user_obj.Current_Balance += fiat_cash
        try:
            db.add(transaction)
            db.commit()
        except SQLAlchemyError as e:
            print("Error during purchasing:", str(e))
            raise HTTPException(status_code=404, detail="Error during purchasing")
        
        return {"status" : "Success"}
    else:
        return {"status": "Failed", "Reason" : "Not enough holdings"}

@app.get("/users/{uid}/crypto_holdings", tags=["Crypto"])
def get_crypto_holdings(uid:str,  db: Session = Depends(get_db)):
    holdings = db.query(models.CryptoHoldings).filter(models.CryptoHoldings.user_id == uid).all()

    return holdings

@app.get("/users/{uid}/crypto_transactions", tags=["Crypto"])
def crypto_transactions(uid:str,  db: Session = Depends(get_db)):
    holdings = db.query(models.CryptoTransactions).filter(models.CryptoHoldings.user_id == uid).all()

    return holdings

@app.get("/users/{uid}/fiat_transactions", tags=["Crypto"])
def fiat_transactions(uid:str,  db: Session = Depends(get_db)):
    holdings = db.query(models.AccountTransactions).filter(models.CryptoHoldings.user_id == uid).all()

    return holdings