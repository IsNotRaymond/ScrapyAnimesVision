import requests


with requests.Session() as session:

    base_url = 'https://dalaran3.animesvision.biz/2/T/The_God_of_High_School/1080p/AnV-06.mp4/'
    url = 'playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9OC8xMS8yMDIwIDg6MTk6MDcgUE0maGFzaF92YWx1ZT01SWNkUWdNZUxLe' \
          'EdLSUhYbWI2N3p3PT0mdmFsaWRtaW51dGVzPTEyMA=='
    url = url.replace("playlist", 'chunk')

    with open("result.txt", 'w') as file:
        res = session.get(base_url + url)
        file.writelines(res.text)

    with open("result.txt") as file:
        packages = [base_url + line.strip() for line in file.readlines() if '.ts' in line]

    #print(packages)

    with open("teste.mp4", "wb") as file:
        res = session.get(packages[1])
        file.write(res.content)
