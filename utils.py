import socks
import socket
import http.cookiejar as cookielib
import mechanize

start = ['/animes/', '/filmes/', '/doramas/', '/cartoons/', '/live-actions/']

ANIMES_VISION = 'http://animesvision.biz'
PATTERN_ALL_SERIES = '/all-series?page='
PATTERN_CARTOONS = '/cartoons?page='
PATTERN_DORAMAS = '/doramas?page='
PATTERN_LIVEACTION = '/live-actions?page='
PATTERN_MOVIES = '/filmes?page='


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

    # patch the socket module
    socket.socket = socks.socksocket
    socket.create_connection = _create_connection

    cookie = cookielib.CookieJar()
    browser = mechanize.Browser()

    browser.set_handle_robots(False)
    browser.set_handle_referer(False)
    browser.set_handle_refresh(True)
    browser.set_handle_redirect(True)
    browser.addheaders = [('User-Agent',
                           'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/80.0.3987.87 Safari/537.36'),
                          ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8'),
                          ('Accept-Language', 'pt,pt-BR;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,de;q=0.5'),
                          ('Accept-Encoding', 'gzip'),
                          ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
                          ('Keep-Alive', '115'),
                          ('Connection', 'keep-alive'),
                          ('Cache-Control', 'max-age=0'),
                          ('Referer', 'http://ouo.io')]

    browser.set_cookiejar(cookie)

    # print(browser.open('https://check.torproject.org/').read())

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
        array = start
    for item in array:
        if string.startswith(item):
            return True

    return False

