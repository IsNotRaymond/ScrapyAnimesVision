import socks
import socket
import os
import http.cookiejar as cookielib
import mechanize
import requests
import json
from tqdm import tqdm
from bs4 import BeautifulSoup


# ANIMES VISION
start_pattern = ['/animes/', '/filmes/', '/doramas/', '/cartoons/', '/live-actions/']

ANIMES_VISION = 'http://animesvision.biz'
PATTERN_ALL_SERIES = '/all-series?page='
PATTERN_CARTOONS = '/cartoons?page='
PATTERN_DORAMAS = '/doramas?page='
PATTERN_LIVEACTION = '/live-actions?page='
PATTERN_MOVIES = '/filmes?page='

# HEADERS PARA ANIMES VISION

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/80.0.3987.87 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8',
           'Accept-Language': 'pt,pt-BR;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,de;q=0.5',
           'Accept-Encoding': 'gzip',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
           'Keep-Alive': '115',
           'Connection': 'keep-alive',
           'Cache-Control': 'max-age=0',
           'Referer': 'http://ouo.io'}


def write_txt(variable, name_file):
    """
    Função que gera um arquivo txt de uma lista contendo dicionarios
    :param variable: a lista de dicionarios
    :param name_file: nome do arquivo a ser salvo
    :return:
    """

    print('Escrevendo em %s' % name_file)

    with open(name_file, 'at') as file:

        for kek in variable:
            file.write(json.dumps(kek) + '\n')

            print('%s escrito' % kek.get('name'))


def _create_connection(address, timeout=None, source_address=None):
    """
    Código pego no stackoverflow para poder utilizar o Tor
    :param address:
    :param timeout:
    :param source_address:
    :return:
    """
    sock = socks.socksocket()
    sock.connect(address)
    return sock


def browser_conf():
    """
    Basicamente nisso aqui ele vai iniciar o serviço Tor e configurar o browser do Mechanize para habilitar requisições.
    Caso tente executar essa função sem que o Tor esteja em execução o programa irá apresentar erro
    :return: retorna o objeto Browser da biblioteca Mechanize
    """
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)

    socket.socket = socks.socksocket
    socket.create_connection = _create_connection

    cookie = cookielib.CookieJar()
    browser = mechanize.Browser()

    browser.set_handle_robots(False)
    browser.set_handle_referer(False)
    browser.set_handle_refresh(True)
    browser.set_handle_redirect(True)
    browser.addheaders = [('User-Agent', HEADERS.get('User-Agent')),
                          ('Accept', HEADERS.get('Accept')),
                          ('Accept-Language',  HEADERS.get('Accept-Language')),
                          ('Accept-Encoding',  HEADERS.get('Accept-Encoding')),
                          ('Accept-Charset',  HEADERS.get('Accept-Charset')),
                          ('Keep-Alive',  HEADERS.get('Keep-Alive')),
                          ('Connection',  HEADERS.get('Connection')),
                          ('Cache-Control',  HEADERS.get('Cache-Control')),
                          ('Referer',  HEADERS.get('Referer'))]

    browser.set_cookiejar(cookie)

    # print(browser.open('https://check.torproject.org/').read()) -> Checar se o browser está configurado no Tor
    return browser


def anime_starts_with(string, array=None):
    """
    Verifica se uma determinada string começa com alguma das substrings contendo no array, uma versão mais poderosa
    da função startswith do python

    :param string: string base
    :param array: array contendo as substrings
    :return: True caso comece com alguma das substrings, False caso contrário
    """
    if array is None:
        array = start_pattern
    for item in array:
        if string.startswith(item):
            return True

    return False


def login_vision():
    """
    Essa funcão irá usar o browser configurado e realizar o login no site do Animes Vision (permitindo os downloads)
    :return: retornará o browser autenticado no site
    """
    browser = browser_conf()
    browser.open('http://animesvision.biz/login')

    browser.select_form(nr=0)
    browser.form['email'] = 'yocalo9921@ofmailer.net'
    browser.form['password'] = os.environ.get('PASSWORD')
    browser.submit()

    return browser


def get_links_vision(browser, start, finish, pattern):
    """
    Essa função irá organizar uma lista com o nome e a url do anime na forma de chave e valor
    :param browser: Objeto da biblioteca Mechanize devidamente logado e configurado
    :param start: começo da pesquisa Nota: As páginas do site precisam ser indexadas por numeros
    :param finish: final da pesquisa
    :param pattern: filtro para a pesquisa Ex: "/all-series?page=", "/cartoons?page="
    :return: retorna a lista completa de animes
    """
    links = []

    for i in range(start, finish + 1):
        url = ANIMES_VISION + pattern + str(i)
        print('Atualmente em: %s' % url)
        browser.open(url)

        for link in browser.links():
            if anime_starts_with(link.url):

                dict_ = extract_name_and_link_vision(link)

                if len(links) == 0:
                    links.append(dict_)
                else:
                    # Site do animes vision é meio desorganizado então eles repetem as urls, então isso é para não repe-
                    # tir no array
                    if links[-1]['name'] != dict_['name']:
                        links.append(dict_)

        print('%d links capturados' % len(links))

    return links


def get_download_and_stream_links_base_vision(browser, url):
    """
    Essa função pega os links de stream e download de um determinado anime e deixa organizado na forma de episódios
    :param browser: o objeto browser da biblioteca Mechanize
    :param url: a url do determinado anime
    :return: retorna um dicionário com os links de stream e download
    """
    start = 1
    dict_ = {}
    browser.open(url)

    for link in browser.links():
        if 'episodio' in link.url or 'filme-' in link.url:
            dict_[start] = {'stream': link.url, 'download': link.url + '/download'}
            start += 1

    return dict_


def get_real_stream_link_vision(browser, url):
    """
    Pega os links de stream de uma determinada página nas qualidades possíveis
    :param browser: Objeto Browser da biblioteca Mechanize
    :param url: a url do episodio Ex: https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado
    :return: Retorna um dicionario com as qualidades e seu respectivo link de stream
    """

    dict_ = {}

    print('Pesquisando link de stream em %s' % url)
    browser.open(url)
    soup = BeautifulSoup(browser.response().read(), features='html5lib')

    for script in soup.find_all('script', type='application/javascript'):

        string = script.text.replace(');', '')
        string = string.replace('jwplayer("playersd").setup(', '')
        string = string.replace('jwplayer("playerhd").setup(', '')

        if string.startswith('{'):
            array = string.split(',')

            for item in array:
                if item.startswith('file:'):
                    url_stream = item.replace('\'', '').replace('file:', '').replace('playlist', 'chunk')

                    if '480p' in url_stream:
                        dict_['480p'] = url_stream
                    if '720p' in url_stream:
                        dict_['720p'] = url_stream

    r1 = requests.get(dict_.get('480p').replace('480p', '1080p')).status_code
    r2 = requests.get(dict_.get('720p').replace('720p', '1080p')).status_code

    if r1 != 404:
        dict_['1080p'] = dict_.get('480p').replace('480p', '1080p')

    elif r2 != 404:
        dict_['1080p'] = dict_.get('720p').replace('720', '1080p')

    return dict_


def get_real_download_link_vision(browser, url):
    """
    Pega os links de downloads direto de cada página
    :param browser: Objeto Browser da biblioteca Mechanize
    :param url: url de download https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado/download
    :return:
    """

    dict_ = {'480p': None, '720p': None, '1080p': None}

    print('Pesquisando link de download em: %s' % url)
    browser.open(url)

    for link in browser.links():

        if anime_starts_with(link.url, ['https://down', 'http://down']):

            if '480p' in link.url:
                dict_['480p'] = link.url
            if '720p' in link.url:
                dict_['720p'] = link.url
            if '1080p' in link.url:
                dict_['1080p'] = link.url

    return dict_


def get_all_links_stream_vision(browser, path):
    anime_links = get_download_and_stream_links_base_vision(browser, ANIMES_VISION + path)
    dict_ = {}

    for key in anime_links.keys():
        dict_[key] = get_real_stream_link_vision(browser, anime_links[key].get('stream'))

    return dict_


def extract_name_and_link_vision(link):
    """
    Com o objeto Link da função links() do Mechanize, essa função simples pega apenas os dados relevantes
    :param link: objeto link
    :param url_base: url base do site
    :return: dicionario com duas chaves "name" e "url"
    """
    dictionary = {'name': link.attrs[1][1], 'url-vision': link.url}

    return dictionary


def download(url, name=None):
    """
    Faz o download de um link

    :param url: link direto de download
    :param name: Nome do arquivo caso deseje ser salvo, caso em branco, o arquivo será salvo no nome padrão
    :return: Não existe retorno
    """

    if name is None:
        name = url.split('/')[-1]

    r = requests.get(url, headers=HEADERS, stream=True)
    length = r.headers.get('content-length')

    with open(name, 'ab') as file:
        for data in tqdm(iterable=r.iter_content(chunk_size=1024), total=(int(length) / 1024) + 1, unit='KB'):
            file.write(data)

    print('Download completo')


def scrapy_all_links_vision(browser):
    """
    CUIDADO !!!!!!!!!

    Essa função é perigosa, ela vai varrer o site inteiro do animes vision e adicionar todas as informações em um
    arquivo txt Obs: Crie uma pasta chamada "Vision" no diretório que será executado o arquivo ou irá gerar um erro
    e o seu tempo será desperdiçado
    :param browser: Objeto da classe mechanize devidamente logado e configurado
    :return: Não há retorno
    """
    links_all_series = get_links_vision(browser, 1, 106, PATTERN_ALL_SERIES)
    links_cartoons = get_links_vision(browser, 1, 4, PATTERN_CARTOONS)
    links_movies = get_links_vision(browser, 1, 18, PATTERN_MOVIES)
    links_doramas = get_links_vision(browser, 1, 2, PATTERN_DORAMAS)
    links_live_actions = get_links_vision(browser, 1, 2, PATTERN_LIVEACTION)

    links_all_series = add_downloads_links_in_a_list(browser, links_all_series)
    links_cartoons = add_downloads_links_in_a_list(browser, links_cartoons)
    links_movies = add_downloads_links_in_a_list(browser, links_movies)
    links_doramas = add_downloads_links_in_a_list(browser, links_doramas)
    links_live_actions = add_downloads_links_in_a_list(browser, links_live_actions)

    write_txt(links_all_series, os.getcwd() + '\\Vision\\animes.txt')
    write_txt(links_cartoons, os.getcwd() + '\\Vision\\cartoons.txt')
    write_txt(links_movies, os.getcwd() + '\\Vision\\movies.txt')
    write_txt(links_doramas, os.getcwd() + '\\Vision\\doramas.txt')
    write_txt(links_live_actions, os.getcwd() + '\\Vision\\live_action.txt')


def add_downloads_links_in_a_list(browser, array):
    """
    Essa função irá adicionar os links diretos de stream e de download dada uma lista com dicionarios contendo a url
    :param browser: O browser devidamente configurado
    :param array: array de dicionarios no seguinte modelo [{'name': 'xx', 'url-vision': 'xx'}]
    :return: será retornado um array de dicionario da seguinte forma [{'name': 'xx',
                                                                       'url-vision': xx
                                                                       'links': {1: {'stream-br': 'xx',
                                                                                      'download-br': 'xx',
                                                                                     }
                                                                                 }
                                                                       }]
    """
    new_array = []

    for dict_ in array:
        links = get_download_and_stream_links_base_vision(browser, dict_.get('url-vision'))

        dict_['links'] = add_real_stream_and_download_links_in_a_dict(browser, links)
        new_array.append(dict_)

    return new_array


def add_real_stream_and_download_links_in_a_dict(browser, dict_):
    """
    Dado um dicionario contendo o link base de download e de stream, essa funcao irá substitui-los pelos links
    diretos
    :param browser: Browser devidamente configurado
    :param dict_: dicionario contendo o link base de download e de stream
    :return: dicionario contendo os links diretos de download e de stream
    """
    new_dict = {}

    for episode in dict_.keys():
        dict_download = get_real_download_link_vision(browser, dict_.get(episode).get('download'))
        dict_stream = get_real_stream_link_vision(browser, dict_.get(episode).get('stream'))

        new_dict[episode] = {'stream-br': dict_stream, 'download-br': dict_download}

    return new_dict
