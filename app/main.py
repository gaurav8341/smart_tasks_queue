# main.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import os

from routes.job_routes import router

# from app.database import get_db

app = FastAPI()

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Smart Task Queue System API is up!"}


