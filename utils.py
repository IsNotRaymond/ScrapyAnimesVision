import socks
import socket
import os
import http.cookiejar as cookielib
import mechanize
import requests
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
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
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


def login_animes_vision():
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


def get_links_animes_vision(browser, start, finish, site, pattern):
    """
    Essa função irá organizar uma lista com o nome e a url do anime na forma de chave e valor
    :param browser: Objeto da biblioteca Mechanize devidamente logado e configurado
    :param start: começo da pesquisa Nota: As páginas do site precisam ser indexadas por numeros
    :param finish: final da pesquisa
    :param site: url base do site "http://animesvision.biz"
    :param pattern: filtro para a pesquisa Ex: "/all-series?page=", "/cartoons?page="
    :return: retorna a lista completa de animes
    """
    links = []

    for i in range(start, finish + 1):
        url = site + pattern + str(i)
        print('Pesquisando Atualmente: %s' % url)
        browser.open(url)

        for link in browser.links():
            if anime_starts_with(link.url):

                dict_ = extract_name_and_link(link, site)

                if len(links) == 0:
                    links.append(dict_)
                else:
                    # Site do animes vision é meio desorganizado então eles repetem as urls, então isso é para não repe-
                    # tir no array
                    if links[-1]['name'] != dict_['name']:
                        links.append(dict_)

        print('%d links capturados' % len(links))

    return links


def get_download_and_stream_links_base(browser, url):
    """
    Essa função pega os links de stream e download de um determinado anime e deixa organizado na forma de episódios
    :param browser: o objeto browser da biblioteca Mechanize (devidamente logado)
    :param url: a url do determinado anime
    :return: retorna um dicionário com os links de stream e download
    """
    start = 1
    dict_ = {}
    browser.open(url)

    for link in browser.links():
        if 'episodio' in link.url:
            dict_[start] = {'stream': link.url, 'download': link.url + '/download'}
            start += 1

    return dict_


def get_real_stream_link(browser, url):
    """
    Pega os links de stream de uma determinada página nas qualidades possíveis
    :param browser: Objeto Browser da biblioteca Mechanize
    :param url: a url do episodio Ex: https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado
    :return: Retorna um dicionario com as qualidades e seu respectivo link de stream
    """

    dict_ = {'480p': None, '720p': None, '1080p': None}

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
                    url_stream = item.replace('\'', '').replace('file:', '')

                    if '480p' in url_stream:
                        dict_['480p'] = url_stream
                    if '720p' in url_stream:
                        dict_['720p'] = url_stream

    if dict_['720p'] is not None:
        dict_['1080p'] = dict_.get('720p').replace('720p', '1080p')

    return dict_


def get_real_download_link(browser, url):
    """
    Pega os links de downloads direto de cada página
    :param browser: Objeto Browser da biblioteca Mechanize
    :param url: url de download https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado/download
    :return:
    """
    dict_ = {'480p': None, '720p': None, '1080p': None}
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


def extract_name_and_link(link, url_base):
    """
    Com o objeto Link da função links() do Mechanize, essa função simples pega apenas os dados relevantes
    :param link: objeto link
    :param url_base: url base do site
    :return: dicionario com duas chaves "name" e "url"
    """
    dictionary = {'name': link.attrs[1][1], 'url': url_base + link.url}

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

    print(length)

    with open(name, 'ab') as file:
        for data in tqdm(iterable=r.iter_content(chunk_size=1024), total=(int(length) / 1024) + 1, unit='KB'):
            file.write(data)

    print('Download completo')

