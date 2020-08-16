from mongo import *
from utils import *


def main():
    mongo = ConnectionDB(DATABASE_NAME, LIST_ANIMES)
    browser = login_vision()

    # swap_boolean(mongo.get_collection(), ['/animes/11eyes', '/animes/12-sai-chicchana-mune-no-tokimeki'])

    # links = get_links_vision(browser, 1, 5, '/ultimas-adicionadas?page=')

    # add_in_list_animes(mongo.get_collection(), links)

    anime_links = get_download_and_stream_links_base_vision(browser, ANIMES_VISION + '/animes/11eyes')
    dict_ = {}

    for key in anime_links.keys():
        dict_[key] = get_real_stream_link_vision(browser, anime_links[key].get('stream'))

    print(dict_)

    # print(get_real_stream_links(browser,
    # 'https://animesvision.biz/animes/the-god-of-high-school/episodio-06/legendado'))

    # soup = BeautifulSoup(browser.response().read(), features='html5lib')
    # soup.prettify()
    # print(soup)

    # "https://down1.animesvision.com.br/freevision/7NnNWOXQVn1QPzpshXXkbA/1597177886/mulWs8p6oiO9lXCgosI4/2/D/Dorohedoro_Dublado/720p/AnV-01.mp4"


main()
