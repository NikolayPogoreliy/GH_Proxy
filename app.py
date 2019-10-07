import re
import requests

from htmldom import htmldom
from flask import Flask, request, Response

app = Flask(__name__)

SITE_NAME = 'https://habr.com/'


def __get_response_content(response: requests.Response) -> str:
    try:
        return response.content.decode()
    except UnicodeDecodeError:
        return ''


def __process_texts(content: str) -> str:
    dom = htmldom.HtmlDom().createDom(content)
    post_div_list = dom.find('div.post__text').nodeList
    uniq_6 = set()
    for post_div in post_div_list:
        uniq_6.update(re.findall(r'[-\'\"«>\s]+([a-zA-Zа-яА-Я]{6})[-\'\"»<,.\s]+', post_div.getText()))
    for w in uniq_6:
        content = re.sub(rf'\b{w}\b', w + '&trade;', content)
    return content


def __process_links(rqs: request,  content: str) -> str:
    return content.replace(f'{SITE_NAME}', f'{rqs.url_root}')


@app.route('/')
def index():
    return proxy('')


@app.route('/<path:path>')
def proxy(path):
    global SITE_NAME
    if request.method == 'GET':
        resp = requests.get(f'{SITE_NAME}{path}')
        cont = __get_response_content(resp)
        if cont:
            cont = __process_texts(cont)
            cont = __process_links(request, cont)
            resp._content = cont.encode()
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers)
    else:
        response = Response('<html>'
                            '<p style="text-align: center;">Oops! It seems that only GET-requests are supported...</p>'
                            '</html>'.encode(), 405)
        return response


if __name__ == '__main__':
    app.run(debug=False, port=1234)
