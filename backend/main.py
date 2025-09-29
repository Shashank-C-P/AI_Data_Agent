from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
from typing import Optional

import agent

app = FastAPI(title="AI Data Agent API")

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    filename: Optional[str] = None

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(TEMP_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"Saved file: {file.filename}")
    return {"filename": file.filename}

@app.post("/query/")
async def handle_query(request: QueryRequest):
    print(f"Received query: {request.question}, for file: {request.filename}")
    file_path = os.path.join(TEMP_DIR, request.filename) if request.filename else None
    
    answer_object = agent.get_answer(file_path=file_path, question=request.question)
    
    return answer_object

