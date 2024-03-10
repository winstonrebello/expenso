
#https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}.BSE&outputsize=full&apikey={api_key}
# 0AVYT7DWA7L71C18
#1---------------------------------------------------------
# from sqlalchemy import create_engine
# from sqlalchemy.orm import scoped_session, sessionmaker
# from flask import Flask, jsonify, redirect, render_template, request, session

# engine = create_engine("postgres://postgres:Winston()@localhost:5432/postgres")
# db = scoped_session(sessionmaker(bind=engine))

# result =db.execute("select * from categories").fetchone()
# print(result)

#2---------------------------------------------------------
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


#####################################################
#List -----------------------------------------------
# my_list = ["one","two",'three',"four",'five','6','7','8','9']
# my_list[2]= 'new_item'
# my_list.append('10')
# my_2_lisy = ['alfa','beta','gama']
# my_2_lisy.insert(3,'hexa')
# my_list.extend(my_2_lisy)
# my_list.sort()
# for i in range(len(my_list)):
#     print(my_list[i])

# fruits = ["apple", "banana", "cherry", "kiwi", "mango"]
# newlist = [x for x in fruits if "a" in x]
# print(newlist)

#####################################################
#Tuple -----------------------------------------------

#NOT a tuple
# thistuple = tuple(("apple","banana","cat","dog"))
# print(type(thistuple))
# print(thistuple[-2:-1])
