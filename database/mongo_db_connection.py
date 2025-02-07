import os
from dotenv import load_dotenv
from pymongo import MongoClient


class MongoDBDAO:
    def __init__(self):
        """
        Initializes a MongoDB DAO (Data Access Object) for CRUD operations.
        """
        # Load environment variables
        load_dotenv()
        self.uri = os.getenv("DATABASE_URL")
        self.client = MongoClient(self.uri)
        self.database_name = os.getenv("DATABASE_NAME")
        self.database = self.client[self.database_name]

    def find(self, collection_name, query, projection=None):
        return list(self.database[collection_name].find(query, projection))

    def find_one(self, collection_name, query, projection=None):
        return self.database[collection_name].find_one(query, projection)

    def insert(self, collection_name, document):
        return self.database[collection_name].insert_one(document)

    def update(self, collection_name, query, update_values, upsert=False):
        return self.database[collection_name].update_one(query, {'$set': update_values}, upsert=upsert)