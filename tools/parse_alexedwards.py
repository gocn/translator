import re

from lxml import etree

from tools.common import get_html, replace_sign, download_image


def parse(url, file):
    text = get_html(url)
    article = etree.HTML(text).xpath('//article')[0]
    article_text = etree.tostring(article, pretty_print=True, method='html').decode("utf-8")

    article_text = re.sub(r'<figure class="file"><figcaption>(.*?)</figcaption><code><pre>(.*?)</pre></code></figure>', r'```file\n/* \1 */\n\2```', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<figure class="(.*?)"><code><pre>(.*?)</pre></code></figure>', r'```\1\2```', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<code>(.*?)</code>', r'`\1`', article_text)
    article_text = re.sub(r'<em>(.*?)</em>', r'*\1*', article_text)
    article_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', article_text)
    article_text = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', article_text, flags=re.DOTALL)
    article_text = re.sub(r'<h1(.*?)>(.*?)</h1>', r'# \2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<h2(.*?)>(.*?)</h2>', r'## \2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<h3(.*?)>(.*?)</h3>', r'### \2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<h4(.*?)>(.*?)</h4>', r'#### \2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<p>(.*?)</p>', r'\1', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<li>(.*?)</li>', r'- \1', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<ul>(.*?)</ul>', r'\1', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<ol (.*?)>(.*?)</ol>', r'\2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<ol>(.*?)</ol>', r'\1', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<samp>(.*?)</samp>', r'\1', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<div(.*?)>(.*?)</div>', r'\2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = re.sub(r'<span(.*?)>(.*?)</span>', r'\2', article_text, flags=re.MULTILINE | re.DOTALL)
    article_text = replace_sign(article_text)

    folder = './static/images' + file.lower().replace('.md', '').replace('-', '_')
    for img in re.findall(r'<img src="(.*?)">', article_text):
        if not img:
            continue
        filename = download_image(f'https://www.alexedwards.net{img}')
        article_text = re.sub(r'<img src="(.*?)">', f'![]({folder}/{filename})', article_text)
    print(article_text)


if __name__ == '__main__':
    parse('https://www.alexedwards.net/blog/an-overview-of-go-tooling', 'an-overview-of-go-tooling')
