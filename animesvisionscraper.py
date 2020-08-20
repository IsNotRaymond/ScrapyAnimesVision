import re
import os
import requests
from tqdm import tqdm
from browser import Browser
from mechanize.polyglot import HTTPError, URLError
from exception import PathIsEmpty, NotHasStreamLinks
from mongoconnect import MongoConnect
from bs4 import BeautifulSoup


class AnimesVisionScraper:
    """
    Classe para fazer a raspagem dos links de stream (download não implementado por causa de um bloqueio no servidor de
    les) e posteriormente adicionar os dados no mongoDB

    Ao ser utilizado pela primeira vez, certifique-se de que suas variáveis de ambiente estão configuradas corretamente
    Nesta classe é solicitada apenas a variável abaixo

    DB_NAME: Nome do banco de dados do mongoDB
    """
    def __init__(self, start=1, finish=1):
        """
        Construtor da classe, não é necessário passar nenhum argumento, mas poderá modificar o inicio e o final da pesqu
        isa no site

        OBS:
        modifique a variável _DEBUG abaixo para False caso deseje desativar as mensagens de log na tela
        """
        self._browser = Browser().setup()
        self.path = []
        self._start = start
        self._finish = finish
        self._database = MongoConnect(str(os.environ.get('DB_NAME')))
        self._DEBUG = True
        self._ANIMES_VISION = 'http://animesvision.biz'
        self._PATTERN_RECENTLY = '/ultimas-adicionadas?page='

    def run(self, all_site=False):
        """
        Função principal que percorre um conjunto de páginas (Caso tenha instanciado a classe sem passar nada, irá ser p
        esquisada apenas os animes contidos na página 'http://animesvision.biz/ultimas-adicionadas?page=1') e adicionar
        os dados em um array, quando toda pesquisa for completada, irá iniciar o processo para salvar no banco de dados.
        por último, o banco de dados vai ser escaneado para verificar os animes com a lista de episódios desatualiza
        :param all_site: Verifica se a pesquisa está sendo feita no site inteiro, caso afirmativo, não será necessário
        utilizar a função __update_not_completed()
        :return:
        """
        self.set_animes()
        self.set_stream_links()
        self.save_on_db()

        if not all_site:
            self.__update_not_completed()

    def run_all_site(self, start=1, finish=131):
        """
        Faz a mesma coisa que a função principal, mas que percorre o site inteiro (Com base que o fim é na página 131)
        :param start: Início da pesquisa
        :param finish: Fim da pesquisa
        :return:
        """
        self._start = start
        self._finish = finish
        self.run(True)

    def set_animes(self):
        """
        Função pública que adiciona os "paths" na forma de dicionário, na variável self.path
        :return:
        """
        self.__scan_all_paths(self._start, self._finish)

    def set_stream_links(self):
        """
        Função pública que coloca os links de stream em seu determinado dicionário contido na variável self.path
        :return:
        """
        self.__path_is_empty()
        self.__set_stream_links()

    def save_on_db(self):
        """
        Função pública que adiciona os dados de self.path nas duas coleções do banco de dados (list_animes e links_visio
        n)
        :return:
        """
        self.save_on_list_animes()
        self.save_on_links_vision()

    def save_on_list_animes(self):
        """
        Função pública que adiciona os dados especificamente na coleção list_animes
        :return:
        """
        self.__path_is_empty()

        for dict_ in self.path:
            document = {'path': dict_.get('path'),
                        'inQueue': False,
                        'isStreamComplete': False,
                        'isDownloadComplete': False}

            self.__save_on_list_animes(document)

    def save_on_links_vision(self):
        """
        Função púbica que adiciona os dados especificamente na coleção links_vision
        :return:
        """
        self.__not_has_stream_links()

        for dict_ in self.path:
            self.__switch_inqueue(dict_, True)
            self.__save_on_links_vision(dict_)
            self.__switch_inqueue(dict_, False)

    def scan_database(self):
        """
        Função pública para escanear os animes que possuem episódios desatualizados
        :return:
        """
        self.__update_not_completed()

    def __switch_inqueue(self, document, boolean):
        """
        Função que altera o atributo inQueue na coleção list_animes, o atributo inQueue serve para mostrar (caso haja) p
        ara outro usuário que aquele documento já está sendo alterado no momento
        :param document: documento contendo as informações
        :param boolean: booleano a ser salvo no banco de dados
        :return:
        """
        self._database.update('list_animes',
                              self._database.search_one('list_animes', 'path', document.get('path')),
                              'inQueue', boolean)
        self.__debug(document.get('path'), 'InQueue %s' % boolean)

    def __scan_not_completed(self):
        """
        Essa função pega todos as informações contidas na coleção e verifica uma por uma, adicionando aquelas cujo episó
        dios estejam desatualizados, no array "not_completed"
        :return: retorna o array "not_completed" contendo os atributos 'path', 'name', 'links' e 'array', onde este últi
        mo é um array contendo a url dos episódios que estão faltando no banco de dados
        """
        query = self._database.get_list('links_vision', ['path', 'name', 'links'])
        not_completed = []
        count = 1

        for item in query:
            dict_ = {'path': item.get('path'), 'name': item.get('name')}

            episodes = item.get('links').get('stream')
            array = self.__get_links_from_path(dict_, 1)

            amount_episodes = len(episodes)
            amount_array = len(array)

            if amount_array > amount_episodes:
                difference = amount_array - amount_episodes
                item['array'] = array[amount_array - difference:amount_array]
                not_completed.append(item)

            count += 1
            self.__debug(count, 'animes já analisados')

        self.__debug('%d' % len(not_completed), 'animes desatualizados')
        return not_completed

    def __update_not_completed(self):
        """
        Dado um array contendo os animes que estão desatualizados, esta função irá pesquisar os novos links e atualizá-
        los no self.path, posteriormente salvando as informações no banco de dados

        OBS:
        Esta função irá modificar o self.path (A fim de ficar mais fácil a obtenção de dados) para conter apenas o anime
        que está sendo pesquisado, ou seja, esta função deve ser executada apenas depois que você tiver salvo os dados c
        ontidos no self.path
        :return:
        """
        array = self.__scan_not_completed()

        for item in array:
            self.path = []
            self.path.append({'name': item.get('name'), 'path': item.get('path')})
            episodes = item.get('links').get('stream')
            self.__set_stream_links_base(self.path[0], item.get('array'), len(episodes) + 1)

            doc = self.path[0]
            stream = doc.get('stream')

            for key in stream.keys():
                episodes[key] = stream.get(key)

            self._database.update('links_vision',
                                  self._database.search_one('links_vision', 'path', doc.get('path')),
                                  'links', {'stream': episodes})

            self.__debug(doc.get('name'), 'Links foram atualizados')

    def __save_on_list_animes(self, document):
        """
        Esta função serve para salvar determinado documento na coleção list_animes
        :param document: Documento a ser salvo
        :return:
        """
        query = self._database.search_one('list_animes', 'path', document.get('path'))

        if query is None:
            self._database.save('list_animes', document)
            self.__debug(document.get('path'), 'salvo no banco')
        else:
            self.__debug(document.get('path'), 'já está salvo no banco')

    def __save_on_links_vision(self, document):
        """
        Esta função serve para salvar determinado documento na coleção links_vision
        :param document: Documento a ser salvo
        :return:
        """
        query = self._database.search_one('links_vision', 'path', document.get('path'))

        if query is None:
            q = self._database.search_one('list_animes', 'path', document.get('path'))
            new_doc = {
                'name': document.get('name'),
                'path': document.get('path'),
                'links': {
                    'stream': document.get('stream')
                }
            }
            self._database.save('links_vision', new_doc)
            self._database.update('list_animes', q, 'isStreamComplete', True)
            self.__debug(document.get('path'), 'salvo no links_vision')

        else:
            if len(query.get('links').get('stream')) == len(document.get('stream')):
                self.__debug(document.get('path'), 'lista de episodios já atualizada')
                return
            else:
                self._database.update('links_vision', query, 'links', {'stream': document.get('stream')})
                self.__debug(document.get('path'), 'lista de episodios foi atualizada com sucesso')

    def __get_list_animes(self, pattern, string):
        """
        Pesquisa a lista de animes de uma determinado página e salva no array self.path
        :param pattern: determinação de onde deve ser pesquisado, caso não seja modificado, irá ser utilizado o "ultimas
        -adicionadas?page="
        :param string: identificador da página Ex: 1, 2, 3 (o nome é string porque é uma string kek)
        :return:
        """
        url = self._ANIMES_VISION + pattern + string
        soup = self.__get_soup(url)

        anchor = soup.find_all('a', {'class': 'thumb'})

        for item in anchor:
            dict_ = {'path': item['href']}

            self.path.append(dict_)

    def __scan_all_paths(self, start, finish):
        """
        Pesquisa a lista de animes de um determinado intervalo de páginas o Padrão é 1-1 (Pesquisa apenas na primeira pá
        gina)
        :param start: Inicio da paginação
        :param finish: Fim da paginação
        :return:
        """
        for i in range(start, finish + 1):
            url = self._ANIMES_VISION + self._PATTERN_RECENTLY + str(i)
            self.__get_list_animes(self._PATTERN_RECENTLY, str(i))

            self.__debug('Pesquisando em', url)

    def __get_links_from_path(self, dict_, magic_number):
        """
        Esta função pega os links de stream (ou download), e adiciona numa lista
        :param dict_: Dicionário que está contido no array self.path
        :param magic_number: 1 para retornar os links de stream, qualquer outro para retornar os links de download
        :return: array contendo os links de stream ou download
        """
        self.__debug('Analisando', dict_.get('path'))
        links_stream = []
        links_download = []

        url = self._ANIMES_VISION + dict_.get('path')

        soup = self.__get_soup(url)
        name = soup.find('h1', class_="dc-title").text
        dict_['name'] = name

        episodes_div = soup.find('div', id='episodes-list')
        anchor_tag = episodes_div.find_all('a', class_='btn btn-sm btn-go2')

        for a in anchor_tag:
            if re.search('download', a['onclick']) is None:
                links_stream.append(self.__get_onclick(a['onclick']))
            else:
                links_download.append(self.__get_onclick(a['onclick']))

        return links_stream if magic_number == 1 else links_download

    def __set_stream_links(self):
        """
        Função que serve para setar os links diretos de stream (cuja extensão sejam de arquivos m3u8) no array self.path
        :return:
        """
        for item in self.path:
            self.__set_stream_links_base(item)

    def __set_stream_links_base(self, document, links=None, count=None):
        """
        Dado um certo dicionario (especificamente aqueles que estão contidos no array self.path) serão pesquisados os
        links diretos de stream (extensão m3u8) e setados no mesmo dicionário dentro do self.path
        :param document: Dicionário contido dentro do self.path
        :param links: argumento opcional que especifica os links a serem pesquisados
        :param count: altera o contador inicial
        :return:
        """
        dict_ = {}

        if count is None:
            count = 1
        if links is None:
            links = self.__get_links_from_path(document, 1)

        for episode in links:
            dict_[str(count)] = self.__get_stream_from_path(episode)
            count += 1

        document['stream'] = dict_

    def __get_stream_from_path(self, url):
        """
        Esta função pega os links de stream de uma certa url e as adiciona em um dicionário separados por qualidade,
        também é verificada se existe uma qualidade melhor
        :param url: url a ser pesquisada
        :return: dicionario contendo as urls separadas por qualidade
        """
        soup = self.__get_soup(url)
        dict_ = {}
        script = soup.find_all('script', type='application/javascript')

        for s in script:
            if s.contents:
                result = re.findall(r"(file:'(.*mp4[^',]*))", s.contents[0])
                if len(result) > 0:
                    link = result[0][1]
                    if '480p' in link:
                        dict_['480p'] = link.replace('playlist', 'chunk')
                    elif '720p' in link:
                        dict_['720p'] = link.replace('playlist', 'chunk')

        self.__debug(url, 'analisado')

        return self.__test_1080p(dict_)

    def __test_1080p(self, dict_):
        """
        Esta função verifica se a qualidade 1080p está disponível para determinado anime
        :param dict_: Dicionário de qualidades para que seja feita a verificação
        :return:
        """
        url_480p = dict_.get('480p').replace('480p', '1080p').replace('chunk', 'playlist')
        url_720p = ''

        if dict_.get('720p') is not None:
            url_720p = dict_.get('720p').replace('720p', '1080p').replace('chunk', 'playlist')

        if self.__found(url_480p):
            dict_['1080p'] = url_480p
            return dict_
        elif url_720p != '':
            if self.__found(url_720p):
                dict_['1080p'] = url_720p
                return dict_

        return dict_

    def __get_soup(self, url):
        """
        Apenas retorna a BeautifulSoup de uma determinada url
        :param url: url a ser pesquisada
        :return: classe BeautifulSoup
        """
        self._browser.open(url)
        response = self._browser.response()
        return BeautifulSoup(response.read(), 'html.parser')

    def __debug(self, phrase, parameter):
        """
        Função que apenas serve para printar algo na tela (Há muitos casos de debug). Será necessário que seja trocada a
        variável self._DEBUG para False, se fossem utilizados vários prints, iria dar muito mais trabalho apagar todos
        :param phrase: qualquer coisa que voce deseje mostrar na tela
        :param parameter: qualquer coisa que voce deseje mostrar na tela
        :return:
        """
        if self._DEBUG:
            print('%s %s' % (phrase, parameter))

    def __path_is_empty(self):
        """
        Verifica se o array self.path está vazio, caso positivo irá ser lançada uma exceção
        :return:
        """
        if len(self.path) < 1:
            raise PathIsEmpty

    def __not_has_stream_links(self):
        """
        Verifica se os links de stream estão setados corretamente, caso contrário irá ser lançada uma exceção
        :return:
        """
        self.__path_is_empty()

        for item in self.path:
            if item.get('stream') is None:
                raise NotHasStreamLinks

    def __found(self, url):
        """
        Verifica se o código da requisição foi 200, caso haja alguma exceção irá ser tratado como outro valor
        :param url: url a ser pesquisada
        :return: retorna True caso o código da requisição for 200, e False em qualquer outra possibilidade
        """
        try:
            response = self._browser.open(url)
            return response.code == 200
        except HTTPError:
            return False
        except URLError:
            return False

    @staticmethod
    def __get_onclick(string):
        """
        Retorna o link contido dentro de um "window.open()"
        :param string: string a ser pesquisada
        :return: retorna uma string contendo o que está dentro de um onclick
        """
        return re.findall(r"'(.*?)'", string)[0]

    @staticmethod
    def download(url, name=None):
        """
        Função utilizada para fazer download de um certo link do animes vision sem o erro 403
        :param url: url de download direto
        :param name: nome do arquivo a ser salvo
        :return:
        """
        if name is None:
            name = url.split('/')[-1]

        r = requests.get(url, headers=Browser().headers, stream=True)
        length = r.headers.get('content-length')

        with open(name, 'ab') as file:
            for data in tqdm(iterable=r.iter_content(chunk_size=1024), total=(int(length) / 1024) + 1, unit='KB'):
                file.write(data)

        print('Download completo')
