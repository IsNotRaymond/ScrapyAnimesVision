from utils import *


def main():
    browser = login_animes_vision()

    download(browser, 'https://down4.animesvision.com.br/freevision/TMlkUpojEYHUrmiaNEYJ_g/1597194373'
                      '/Z1C1gbKDKNDqBdk42WVF/1/N/naruto/480p/AnV-01.mp4')

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
