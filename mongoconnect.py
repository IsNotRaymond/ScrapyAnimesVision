import os
from pymongo import MongoClient


class MongoConnect:
    """
    Classe criada com o intuito de facilitar a conexão ao banco de dados em outros pacotes, note que para usá-lo, seu
    cluster do mongodb (Neste caso está sendo usado o Atlas) deve estar configurado nas variáveis abaixo

    MONGO_URL: A string de conexão do banco de dados
    """

    def __init__(self, db_name, atlas=True):
        """
        Construtor da classe
        :param db_name: Nome do database a ser utilizado
        :param atlas: Caso esteja usando um cluster online, será adicionada uma string para a conexão funcionar de forma
        adequada
        """
        self.db_name = db_name
        self.__url = os.environ.get('MONGO_URL')

        if atlas:
            self.__url += 'test?retryWrites=true&w=majority'

    def get_collection(self, collection_name):
        """
        Função que retorna a coleção do banco de dados instanciado
        :param collection_name: o nome da coleção
        :return: coleção do banco de dados
        """
        client = MongoClient(self.__url)
        db = client[self.db_name]
        return db[collection_name]

    def save(self, collection_name, document):
        """
        Salva um documento em uma coleção
        :param collection_name: nome da coleção
        :param document: documento a ser salvo
        :return:
        """
        collection = self.get_collection(collection_name)
        collection.insert_one(document)

    def update(self, collection_name, query, attribute, value):
        """
        Modifica um certo atributo de uma coleção
        :param collection_name: nome da coleção
        :param query: identificação para o documento a ser modificado, pode ser utilizada a função search_one abaixo
        :param attribute: Campo a ser modificado
        :param value: novo valor do campo
        :return:
        """
        collection = self.get_collection(collection_name)
        collection.update(query, {"$set": {attribute: value}})

    def search_one(self, collection_name, attribute, value):
        """
        Pesquisa um documento em uma coleção
        :param collection_name: nome da coleção
        :param attribute: atributo de identificação (Caso exista mais de uma ocorrência, irá retornar a primeira)
        :param value: valor do atributo acima
        :return: retorna um documento com todas as informações
        """
        collection = self.get_collection(collection_name)
        return collection.find_one({attribute: value})

    def get_list(self, collection_name, fields):
        """
        Pega a lista completa de elementos de uma certa coleção, mas nesse caso é necessário especificar os campos que
        você deseja, o _id será sempre ocultado
        :param collection_name: nome da coleção
        :param fields: deve ser um array contendo um ou mais elementos
        :return: retorna uma lista de dicionarios quando há mais de um elemento no parametro "fields", retorna apenas um
        a lista comum caso haja apenas um elemento no array
        """
        collection = self.get_collection(collection_name)
        projection = {'_id': 0, }

        for item in fields:
            projection[item] = 1

        cursor = collection.find({}, projection)

        if len(fields) == 1:
            return [x[fields[0]] for x in cursor]

        return [x for x in cursor]

    def remove(self, collection_name, items_to_remove, field):
        """
        Remove todos os elementos de uma lista do banco de dados
        :param collection_name: nome da coleção
        :param items_to_remove: lista de itens a ser removidos
        :param field: nome do campo onde consta o certo item na lista acima
        :return:
        """
        collection_name = self.get_collection(collection_name)

        for item in items_to_remove:
            collection_name.find_one_and_delete({field: item})
