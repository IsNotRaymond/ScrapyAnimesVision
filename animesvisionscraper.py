import re
import requests
from tqdm import tqdm
from browser import Browser
from mechanize.polyglot import HTTPError, URLError
from exception import PathIsEmpty, NotHasStreamLinks
from mongoconnect import MongoConnect
from bs4 import BeautifulSoup


class AnimesVisionScraper:
    def __init__(self):
        self._browser = Browser().setup()
        self.path = []
        self.start = 1
        self.finish = 1
        self._database = MongoConnect('Animes-Request')
        self._DEBUG = True
        self._ANIMES_VISION = 'http://animesvision.biz'
        self._PATTERN_RECENTLY = '/ultimas-adicionadas?page='

    def run(self):
        self.set_animes()
        self.set_stream_links()
        self.save_on_db()
        self.__update_not_completed()

    def run_all_site(self, value=131):
        self.finish = value
        self.run()

    def set_animes(self):
        self.__scan_all_paths(self.start, self.finish)

    def set_stream_links(self):
        self.__path_is_empty()
        self.__set_stream_links()

    def save_on_db(self):
        self.save_on_list_animes()
        self.save_on_links_vision()

    def save_on_list_animes(self):
        self.__path_is_empty()

        for dict_ in self.path:
            document = {'path': dict_.get('path'),
                        'inQueue': False,
                        'isStreamComplete': False,
                        'isDownloadComplete': False}

            self.__save_on_list_animes(document)

    def save_on_links_vision(self):
        self.__not_has_stream_links()

        for dict_ in self.path:
            self.__switch_inqueue(dict_, True)
            self.__save_on_links_vision(dict_)
            self.__switch_inqueue(dict_, False)

    def scan_database(self):
        self.__update_not_completed()

    def __switch_inqueue(self, document, boolean):
        self._database.update('list_animes',
                              self._database.search_one('list_animes', 'path', document.get('path')),
                              'inQueue', boolean)
        self.__debug(document.get('path'), 'InQueue %s' % boolean)

    def __scan_not_completed(self):
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
        query = self._database.search_one('list_animes', 'path', document.get('path'))

        if query is None:
            self._database.save('list_animes', document)
            self.__debug(document.get('path'), 'salvo no banco')
        else:
            self.__debug(document.get('path'), 'já está salvo no banco')

    def __save_on_links_vision(self, document):
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
        url = self._ANIMES_VISION + pattern + string
        soup = self.__get_soup(url)

        anchor = soup.find_all('a', {'class': 'thumb'})

        for item in anchor:
            dict_ = {'path': item['href']}

            self.path.append(dict_)

    def __scan_all_paths(self, start, finish):
        for i in range(start, finish + 1):
            url = self._ANIMES_VISION + self._PATTERN_RECENTLY + str(i)
            self.__get_list_animes(self._PATTERN_RECENTLY, str(i))

            self.__debug('Pesquisando em', url)

    def __get_links_from_path(self, dict_, magic_number):
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
        for link in self.path:
            self.__set_stream_links_base(link)

    def __set_stream_links_base(self, link, links=None, count=None):
        dict_ = {}

        if count is None:
            count = 1
        if links is None:
            links = self.__get_links_from_path(link, 1)

        for episode in links:
            dict_[str(count)] = self.__get_stream_from_path(episode)
            count += 1

        link['stream'] = dict_

    def __get_stream_from_path(self, url):
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
        self._browser.open(url)
        response = self._browser.response()
        return BeautifulSoup(response.read(), 'html.parser')

    def __debug(self, phrase, parameter):
        if self._DEBUG:
            print('%s %s' % (phrase, parameter))

    def __path_is_empty(self):
        if len(self.path) < 1:
            raise PathIsEmpty

    def __not_has_stream_links(self):
        self.__path_is_empty()

        for item in self.path:
            if item.get('stream') is None:
                raise NotHasStreamLinks

    def __found(self, url):
        try:
            response = self._browser.open(url)
            return response.code == 200
        except HTTPError:
            return False
        except URLError:
            return False

    @staticmethod
    def __get_onclick(string):
        return re.findall(r"'(.*?)'", string)[0]

    @staticmethod
    def download(url, name=None):

        if name is None:
            name = url.split('/')[-1]

        r = requests.get(url, headers=Browser().headers, stream=True)
        length = r.headers.get('content-length')

        with open(name, 'ab') as file:
            for data in tqdm(iterable=r.iter_content(chunk_size=1024), total=(int(length) / 1024) + 1, unit='KB'):
                file.write(data)

        print('Download completo')
