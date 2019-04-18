import argparse
import re
import uuid
from urllib import parse

import requests


def parse_args():
    parser = argparse.ArgumentParser(description='解析 Markdown.')
    parser.add_argument('--url', type=str, help='源地址')
    parser.add_argument('--file', type=str, help='存储文件名')

    args = parser.parse_args()

    return args.url, args.file


def get_html(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text


def parse_title(text):
    return re.findall(r'<title>(.*?)</title>', text)[0]


def parse_source(url):
    u = parse.urlparse(url)
    return f'{u.scheme}://{u.netloc}'


def parse_github_url(file: 'str'):
    return f'https://github.com/gocn/translator/blob/master/2019/{file.lstrip("./")}'


def replace_sign(t):
    for i in [
        ['&lt;', '<'],
        ['&#8216;', '‘'],
        ['&gt;', '>'],
        ['&#8212;', '—'],
        ['&#8217;', "'"],
        ['&#8230;', '…'],
        ['&#8220;', '“'],
        ['&#8221;', '”']]:
        t = t.replace(i[0], i[1])
    return t


def gen_uuid_filename(f):
    return uuid.uuid4().hex.upper() + '.' + f.split('.')[-1]


def download_image(url):
    filename = gen_uuid_filename(url)
    r = requests.get(url)
    r.raise_for_status()
    with open(filename, 'wb') as f:
        f.write(r.content)
    print('download:', filename)
    return filename


'''# {title}

- 原文地址：[{title}]({url})
- 原文作者：{author}
- 译文出处：{source}
- 本文永久链接：{current_github_url}
- 译者：
- 校对者：

'''
