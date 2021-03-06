import socks
import socket
import http.cookiejar as cookielib
import mechanize
import os


class Browser:
    """
    Classe usada para fazer requisições (normais ou via Tor) no animes vision, para utilizá-la, basta instanciar e rodar
    o método setup(), por exemplo br = Browser().setup()
    OBS:
    Caso queira fazer requisições normais ou não tem o Tor configurado em seu computador, utilize:
    br = Browser(False).setup()

    Variáveis de ambiente necessárias:
    EMAIL: Email para fazer login no Animes Vision
    PASSWORD: Senha de acesso
    """
    def __init__(self, tor=True):
        """
        Construtor da classe, é necessário passar se deseja usar o Tor ou não
        :param tor: booleano para verificação

        OBS:
        os headers abaixo são necessários para fazer requisições de download, caso não houvesse isso iria dar erro 403
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 '
                          'Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8',
            'Accept-Language': 'pt,pt-BR;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,de;q=0.5',
            'Accept-Encoding': 'gzip',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '115',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Referer': 'http://ouo.io'}
        self.tor = tor

    def __browser_conf(self):
        """
        Configuração do browser para que não seja tratado como um robô qualquer
        :return:
        """

        if self.tor:
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)

            socket.socket = socks.socksocket
            socket.create_connection = self._create_connection

        cookie = cookielib.CookieJar()
        browser = mechanize.Browser()

        browser.set_handle_robots(False)
        browser.set_handle_referer(False)
        browser.set_handle_refresh(True)
        browser.set_handle_redirect(True)
        browser.addheaders = [('User-Agent', self.headers.get('User-Agent')),
                              ('Accept', self.headers.get('Accept')),
                              ('Accept-Language', self.headers.get('Accept-Language')),
                              ('Accept-Encoding', self.headers.get('Accept-Encoding')),
                              ('Accept-Charset', self.headers.get('Accept-Charset')),
                              ('Keep-Alive', self.headers.get('Keep-Alive')),
                              ('Connection', self.headers.get('Connection')),
                              ('Cache-Control', self.headers.get('Cache-Control')),
                              ('Referer', self.headers.get('Referer'))]

        browser.set_cookiejar(cookie)

        return browser

    def setup(self):
        """
        Faz o login no site do animes vision (Necessário para pegar os links de download) e retorna o browser com login

        :return:
        """
        browser = self.__browser_conf()
        browser.open('http://animesvision.biz/login')

        browser.select_form(nr=0)
        browser.form['email'] = os.environ.get('EMAIL')
        browser.form['password'] = os.environ.get('PASSWORD')
        browser.submit()

        return browser

    @staticmethod
    def _create_connection(address, timeout=None, source_address=None):
        """
        Código pego no stackoverflow para poder utilizar o Tor. Não sei o que faz
        :param address:
        :param timeout:
        :param source_address:
        :return:
        """
        sock = socks.socksocket()
        sock.connect(address)
        return sock
