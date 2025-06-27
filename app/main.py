# main.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import os

from app.routes import router

# from app.database import get_db

app = FastAPI()

app.include_router()

