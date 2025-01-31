from pymongo import MongoClient

db_client = MongoClient("mongodb+srv://gauravvyas:oFQ46Uomi9XSrl6g@ssp-dev.6s6oi.mongodb.net/")

db = db_client["SSP-dev"]

