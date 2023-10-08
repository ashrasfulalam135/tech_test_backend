from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import models.models as models
from db.database import engine, SessionLocal
from schemas.schemas import SqlParser
from sqlalchemy.orm import Session
from app.dependencies import sqlparser
import os
from dotenv import load_dotenv

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

load_dotenv()
# Configure CORS
origins = [
    os.getenv("ALLOWED_URL"),  # Add your frontend URL here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can restrict this to specific HTTP methods if needed
    allow_headers=["*"],  # You can restrict this to specific headers if needed
)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message" : "Hello World"}

@app.post("/")
def parse_sql(sql_parser: SqlParser, db: Session = Depends(get_db)):
    sqlparser_model = models.SqlParsers()
    
    if not sqlparser(sql_parser.input_query):
        response_data = {
            "input_query": sql_parser.input_query,
            "message": "Invalid Query"
        }
        return JSONResponse(content=response_data)
    
    map,modified_sql = sqlparser(sql_parser.input_query)
    
    sqlparser_model.input_query = sql_parser.input_query
    sqlparser_model.modified_query = modified_sql
    sqlparser_model.hashed_column_map = map
    
    db.add(sqlparser_model)
    db.commit()
    
    response_data = {
        "input_query": sql_parser.input_query,
        "modified_query": modified_sql,
        "hashed_column_map": map
    }
    
    return JSONResponse(content=response_data)
