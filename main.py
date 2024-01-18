import os
import io
import json
import base64
import hashlib
import asyncio 
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Header,Request,File, UploadFile,status,Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse,FileResponse,Response
from typing import Dict,List,Any,Union
from CaesarSQLDB.caesarcrud import CaesarCRUD
from CaesarSQLDB.caesarhash import CaesarHash
from fastapi.responses import StreamingResponse
from fastapi import WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from caesaraicontractqa import CaesarAIContractQA
import pandas as pd
from io import StringIO
from fastapi import WebSocket


load_dotenv(".env")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


JSONObject = Dict[Any, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]

class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        """connect event"""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Direct Message"""
        await websocket.send_json(message)
    
    def disconnect(self, websocket: WebSocket):
        """disconnect event"""
        self.active_connections.remove(websocket)


manager = ConnectionManager()
@app.get('/',response_class=HTMLResponse)# GET # allow all origins all methods.
async def index(request: Request):
        return templates.TemplateResponse( name="home.html",context={"request":request}
    )
@app.post("/changetoquestion")
def changetoquestion( data: JSONStructure = None):
    try:
        data = dict(data)

        caesaraiqa = CaesarAIContractQA(data_text=data["text"])
        #caesaraiqa.create_db_document(data_source_type="PDF")
        caesaraiqa.create_db_document(data_source_type="TXT")
        question = "change this sentence into a question as if you are asking if the subject is up to good standard"
        res  =  caesaraiqa.ask_question(question=question, language="ENGLISH",changetoquestion=True)
        return res
    except Exception as ex:
        return {"error":f"{type(ex)}-{ex}"}

@app.websocket("/changetoquestioncsvws")
async def changetoquestioncsvws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                #print(data)
                csvstr = base64.b64decode(data["file"]).decode()
                TESTDATA = StringIO(csvstr)
                df = pd.read_csv(TESTDATA, sep=",")
                for statement in list(df["statements"]):
                    caesaraiqa = CaesarAIContractQA(data_text=statement)
                    caesaraiqa.create_db_document(data_source_type="TXT")
                    question = "change this sentence into a question as if you are asking if the subject is up to good standard"
                    res  =  caesaraiqa.ask_question(question=question, language="ENGLISH",changetoquestion=True)
                    await manager.send_personal_message(res,websocket)
                await manager.send_personal_message({"result":"finished"},websocket)
            except Exception as ex:
                await manager.send_personal_message({"error":f"{type(ex)}-{ex}"},websocket)

    except WebSocketDisconnect:
        #await manager.send_personal_message({"message":"Bye!!!"},websocket)
        manager.disconnect(websocket)
        
if __name__ == "__main__":
    uvicorn.run("main:app",port=9000,log_level="info")
    #uvicorn.run()
    #asyncio.run(main())