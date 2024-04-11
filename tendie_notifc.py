import os
import calendar

from flask import request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
from helpers import convertSQLToDict

# Create engine object to manage connections to DB, and scoped session to separate user interactions with DB
engine = create_engine("postgres://postgres:Winston()@localhost:5432/postgres")
db = scoped_session(sessionmaker(bind=engine))

