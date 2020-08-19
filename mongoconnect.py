import os
from pymongo import MongoClient


class MongoConnect:
    """
    Classe criada com o intuito de facilitar a conexão ao banco de dados em outros pacotes, note que para usá-lo, seu
    cluster do mongodb (Neste caso está sendo usado o Atlas) deve estar configurado nas variáveis abaixo
    """

    def __init__(self, db_name):
        self.db_name = db_name
        self.__auth = str(os.environ.get('USER')) + ':' + str(os.environ.get('PASSWORD'))
        self.__url = 'mongodb+srv://' + self.__auth + '@mongo-qiim9.gcp.mongodb.net/test?retryWrites=true&w=majority'

    def get_collection(self, collection_name):
        client = MongoClient(self.__url)
        db = client[self.db_name]
        return db[collection_name]

    def save(self, collection_name, document):
        collection = self.get_collection(collection_name)
        collection.insert_one(document)

    def update(self, collection_name, query, attribute, value):
        collection = self.get_collection(collection_name)
        collection.update(query, {"$set": {attribute: value}})

    def search_one(self, collection_name, attribute, value):
        collection = self.get_collection(collection_name)
        return collection.find_one({attribute: value})

    def get_list(self, collection_name, fields):
        collection = self.get_collection(collection_name)
        projection = {'_id': 0, }

        for item in fields:
            projection[item] = 1

        cursor = collection.find({}, projection)

        if len(fields) == 1:
            return [x[fields[0]] for x in cursor]

        return [x for x in cursor]

    def remove(self, collection_name, items_to_remove, field):
        collection_name = self.get_collection(collection_name)

        for item in items_to_remove:
            collection_name.find_one_and_delete({field: item})
