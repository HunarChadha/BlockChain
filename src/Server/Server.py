from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import main
from Database import DataBase

app = FastAPI()

app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_methods=["*"],allow_headers=["*"])

@app.get("/")
def read_root():
    return {"messgae": "Server is Running"}

@app.post("/money")
def receive_hello(data: dict):
    print(main.verify(data))
    return {"reply": f"Server got"}

@app.post("/storeData")
def receive_info(data:dict):
    DataBase.enter_data(data["publicKey"], data["nonce"])
    return "saved"

@app.post("/Test")
def Test1(data:dict):
    DataBase.saveTestData(data)
    return "saved"

@app.post("/Balance")
def Balance(data:dict):
    print(data)
    return DataBase.fetchAllData()