from flask import Flask, request, send_file, flash
from xiumeteo.base.redis import redis_client

from xiumeteo.base.sms import send_filename, check_phone
import requests
import random
import logging
import io

logger = logging.getLogger(__name__)

app = Flask(__name__)

words = requests.get('http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain') \
    .content.decode("utf-8")  \
    .lower() \
    .splitlines()

def word():
  return random.choice(words)

def cache_for_delete(uri):
  from datetime import datetime as time
  redis_client.sadd('cache_for_delete', {'key':uri, 'time':str(time.now())})

def cache_for_serving(uri):
  key = uri + '.served'
  served = redis_client.get(key)
  if served == None:
    redis_client.set(key, 'no')
  if served == b'no':
    redis_client.set(key, 'yes')

def save_type(uri, filename):
  key = uri + '.filename'
  logger.error(key)

  return redis_client.set(key, filename)

def get_type(uri):
  logger.error(uri)
  return redis_client.get(uri + '.filename').decode('utf-8')

def type(filename):
  return filename.rsplit('.', 1)[1].lower()

@app.route('/<phone>', methods=['POST'])
def put(phone='9999471847'):
  try:
    phone = check_phone(phone)
    if not phone:
      flash('Bas request')
    file = request.files['file']
    # logger.error(file)
    if not file:
      return 404
    filename = '{}-{}'.format(word(), word())
    stream = file.stream.read()
    # logger.error(filename) 
    # logger.error(stream) 
    if not stream:
      return 400
    key = '{}.{}'.format(phone, filename)
    saved = redis_client.set(key, stream)
    save_type(key, file.filename)
    if saved:
      cache_for_delete(key)
      send_filename(phone, filename, request.base_url)
      return 'OK'
  except Exception as ex:
    logger.error(ex)
    return str(ex)
  return 400


@app.route('/<phone>/<name>', methods=['GET'])
def get(phone, name):
  key = '{}.{}'.format(phone, name)
  content = redis_client.get(key)
  filename = get_type(key)
  if not filename:
    return 404
  cache_for_serving(key)
  resp = send_file(io.BytesIO(content), attachment_filename=filename) 
  redis_client.delete(key)
  return resp



@app.route('/<phone>', methods=['GET'])
def save(phone):
  return '''
  <!doctype html>
  <title>Upload new File</title>
  <h1>Upload new File</h1>
  <form method=post action='/{}' enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
  </form>
  '''.format(phone)


@app.route('/', methods=['GET'])
def home():
  return '''
  <h1>Upload new File</h1>
  
  '''
  
  
