import re
#import json
import simplejson as json
from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
from newspaper import Article
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://chat.openai.com"}})

@app.route('/')
def home():
    return '/search?q=your+query+here'

@app.route('/search')
def search():
    q = request.args.get('q')
    if not q:
        return error_response('Please provide a query.')

    try:
        q = q[:500]
        q = escape_ddg_bangs(q)
        region = request.args.get('region', 'wt-wt')
        safesearch = request.args.get('safesearch', 'Off')
        time = request.args.get('time', None)
        max_results = request.args.get('max_results', 3, type=int)
        max_results = min(max_results, 10)

        ddgs = DDGS()
        results = ddgs.text(keywords=q, region=region, safesearch=safesearch, timelimit=time, max_results=max_results)
        response = json.dumps(results, iterable_as_array=True)
        resp = Response(response)
        resp.headers['Content-Type'] = 'application/json'
        return resp

    except Exception as e:
        print(e)
        return error_response(f'Error searching: {e}')

def escape_ddg_bangs(q):
    q = re.sub(r'^!', r'', q)
    q = re.sub(r'\s!', r' ', q)
    return q

@app.route('/url_to_text')
def url_to_text():
    url = request.args.get('url')
    if not url:
        return error_response('Please provide a URL.')

    if '.' not in url:
        return error_response('Invalid URL.')

    try:
        title, text, authors, publish_date, top_image, movies = extract_title_and_text_from_url(url)
    except Exception as e:
        return error_response(f'Error extracting text from URL: {e}')

    text = re.sub(r'\n{4,}', '\n\n\n', text)

    response = jsonify([{
        'body': text,
        'href': url,
        'title': title,
        'authors': authors,
        'publish_date': publish_date,
        'top_image': top_image,
        'movies': movies
    }])

    return response

def error_response(message):
    response = jsonify([{
        'body': message,
        'href': '',
        'title': ''
    }])
    
    resp = Response(response)
    resp.status_code = 500
    resp.headers['Content-Type'] = 'application/json'
    return resp

def extract_title_and_text_from_url(url: str):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    article = Article(url)
    article.download()
    article.parse()

    return article.title, article.text, article.authors, article.publish_date, article.top_image, article.movies 
