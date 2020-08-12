import os
import utils
from bs4 import BeautifulSoup


def login_animes_vision():
    """
    Essa funcão irá usar o browser configurado e realizar o login no site do Animes Vision (permitindo os downloads)
    :return: retornará o browser autenticado no site
    """
    browser = utils.browser_conf()
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
            if utils.anime_starts_with(link.url):

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


def get_real_stream_links(browser, url):
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


def get_real_download_links(browser, url):
    """
    Pega os links de downloads direto de cada página
    :param browser: Objeto Browser da biblioteca Mechanize
    :param url: url de download https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado/download
    :return:
    """
    dict_ = {'480p': None, '720p': None, '1080p': None}
    browser.open('url')

    for link in browser.links():

        if utils.anime_starts_with(link.url, ['https://down', 'http://down']):

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


def download(browser, name, url):
    """
    Faz o download do arquivo
    :param browser: Objeto Browser da biblioteca Mechanize
    :param name: nome do arquivo a ser salvo
    :param url: link direto de download
    :return: Não existe retorno
    """

    browser.open(url)

    with open(name, 'ab') as file:
        print('Download iniciado')
        file.write(browser.response().read())


def main():
    browser = login_animes_vision()

    # links = get_links_animes_vision(browser, 1, 106, utils.ANIMES_VISION, utils.PATTERN_ALL_SERIES)

    # kek = get_download_and_stream_links_base(browser, 'https://animesvision.biz/animes/the-god-of-high-school')

    # for key in kek.keys():
    #   print(get_real_stream_links(browser, kek[key].get('stream')))

    # print(get_real_stream_links(browser,
    # 'https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado'))

    # soup = BeautifulSoup(browser.response().read(), features='html5lib')
    # soup.prettify()
    # print(soup)

    # "https://down1.animesvision.com.br/freevision/7NnNWOXQVn1QPzpshXXkbA/1597177886/mulWs8p6oiO9lXCgosI4/2/D/Dorohedoro_Dublado/720p/AnV-01.mp4"


main()
