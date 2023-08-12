from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, jsonify, redirect, render_template, request, session

engine = create_engine("postgres://postgres:Winston()@localhost:5432/postgres")
db = scoped_session(sessionmaker(bind=engine))

result =db.execute("select * from categories").fetchone()
print(result)

#WORKS FINE
# from flask import Flask
 
# # Flask constructor takes the name of
# # current module (__name__) as argument.
# app = Flask(__name__)
 
# # The route() function of the Flask class is a decorator,
# # which tells the application which URL should call
# # the associated function.
# @app.route('/')
# # ‘/’ URL is bound with hello_world() function.
# def hello_world():
#     return 'Hello World'
 
# # main driver function
# if __name__ == '__main__':
 
#     # run() method of Flask class runs the application
#     # on the local development server.
#     app.run()