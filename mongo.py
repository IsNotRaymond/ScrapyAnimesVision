from pymongo import MongoClient
from utils import get_all_links_stream_vision
import os

# VARIÁVEIS SECRETAS DE AMBIENTE
USER = os.environ.get('USER')
PASSWORD = os.environ.get('PASSWORD')

# CONSTANTES
AUTH = str(USER) + ':' + str(PASSWORD)
DATABASE_NAME = 'Animes-Request'
LIST_ANIMES = 'list_animes'
LINKS_VISION = 'links_vision'
URL_SERVER = 'mongodb+srv://' + AUTH + '@mongo-qiim9.gcp.mongodb.net/test?retryWrites=true&w=majority'


class ConnectionDB:
    """
    Classe criada com o intuito de facilitar a conexão ao banco de dados em outros pacotes, note que para usá-lo, seu
    cluster do mongodb (Neste caso está sendo usado o Atlas) deve estar configurado nas variáveis acima
    """

    def __init__(self, db_name, collection_name):
        self.db_name = db_name
        self.collection_name = collection_name

    def get_collection(self):
        client = MongoClient(URL_SERVER)
        db = client[self.db_name]
        return db[self.collection_name]


def main():
    """
    Função principal criada para realizar uma varredura completa no site adicionado cada anime ao banco de dados com o
    intuito de acelelar as buscas no site, por exemplo, caso tenha algum anime com mais de 900 episodios e ele esteja no
    banco de dados, não será necessário esperar vários minutos para os links serem analisados e a resposta será quase
    instantânea. Caso o banco de dados esteja vazio, descomente todas as funções add_in_database, mas tome cuidado pois
    ela consome muito tempo. Caso você tenha adicionado todos os animes, então somente a função scan_not_completed deve-
    rá ser executada, ela atualiza o banco de dados com os animes que ainda não estão completos.

    :return: Vazio
    """
    client = MongoClient(URL_SERVER)
    database = client[DATABASE_NAME]
    list_animes = database[LIST_ANIMES]


"""def get_list(start, finish, pattern):
    Pega a lista de animes paginadas de início ao fim

    :param start: inicio da página de pesquisa
    :param finish: fim da página de pesquisa
    :param pattern: Constante que determina a página a ser pesquisada
    :return: lista contento o nome e a url de cada anime
    count = 1
    list_s = []
    dictionary = {}

    add_in_dict(start, finish, pattern, count, dictionary)

    for item in dictionary.keys():
        list_s.append(dictionary[item])

    return list_s
"""


def get_inqueue(list_query, key):
    for q in list_query:
        if q['path'] == key:
            return q['inQueue']

    return None


def add_in_list_animes(collection, list_to_add):
    """
    Essa função vai preencher os dados da coleção chamada list_animes no cluster do atlas

    :param collection: objeto que representa uma collection do MongoClient
    :param list_to_add: lista de todos os animes contendo nome e url
    :return: Vazio
    """
    query = collection.find({}, {"_id": 0, "path": 1, "inQueue": 1})

    list_complete = [q for q in query]
    list_added = [q['path'] for q in query]

    for dictionary in list_to_add:
        path = dictionary['url-vision']
        in_queue = get_inqueue(list_complete, path)

        if path in list_added:
            print('%s já adicionado' % path)
            continue

        if in_queue:
            print('%s está em uso' % path)
            continue

        document = {'path': path,
                    'inQueue': False,
                    'isDownloadComplete': False,
                    'isStreamComplete': False}

        collection.insert_one(document)
        print('%s adicionado' % dictionary['name'])


def add_in_links_vision(browser, collection_list, collection_links, list_to_add):
    query = collection_list.find({}, {"_id": 0, "path": 1, "inQueue": 1})

    list_complete = [q['path'] for q in query if q['path'] in [i['url-vision'] for i in list_to_add]]

    swap_boolean(collection_list, 'inQueue', list_complete)

    for dict_ in list_to_add:
        document = {
            'name': dict_['name'],
            'path': dict_['url-vision'],
            'links': {'stream': get_all_links_stream_vision(browser, dict_['url-vision'])
                      }
        }

        collection_links.insert_one(document)
        print('%s Adicionado' % dict_['name'])

    swap_boolean(collection_list, 'inQueue', list_complete)


def swap_boolean(collection, name_atribute, list_to_swap):

    for path in list_to_swap:
        q = collection.find_one({'path': path})
        collection.update_one(q, {'$set': {name_atribute: not q[name_atribute]}})

    print('%s modificado' % name_atribute)


"""def scan_not_completed(collection):
    Função que pega os nomes dos animes que não estão completos no banco de dados, e os pesquisa no site, verificando se
    é necessário ou não atualizá-los de acordo com o tamanho da lista de episódios, caso sejam iguais, não será atuali-
    zado

    :param collection: objeto que representa uma collection do MongoClient
    :return:

    list_not_completed = [q['nome'] for q in collection.find({"status": {"$ne": "Status: Completo"},
                                                              "tipo": {"$ne": "filme"}})]

    for name in list_not_completed:
        q = collection.find_one({'nome': name})

        list_links = get_links(BeautifulSoup(requests.get(q['url']).content, 'html.parser'))

        if len(q['links']) == len(list_links):
            print('%s: Nada foi modificado' % name)
        else:
            list_download_links = get_all_download_links(list_links)
            collection.update_one(q, {'$set': {'links': list_download_links}})
            print('%s: Os links foram atualizados com sucesso' % name)

"""
if __name__ == '__main__':
    main()
