from flask import Flask, request, send_file, flash
from xiumeteo.base.redis import redis_client

from xiumeteo.base.sms import send_filename, check_phone, check_auth, auth
import requests
import random
import logging
import io

logger = logging.getLogger(__name__)

app = Flask(__name__)

ALLOWED_FILES = {'jpeg', 'jpg', 'gif', 'pdf', 'doc', 'docx', 'xsx', 'png', 'txt', 'csv'}

words = requests.get('http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain') \
    .content.decode("utf-8")  \
    .lower() \
    .splitlines()

def word():
  return random.choice(words)

def cache_for_delete(uri):
  from datetime import datetime as time
  redis_client.sadd('cache_for_delete', {'key':uri, 'time':str(time.now())})


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
def put(phone):
  try:
    code = request.form['code']
    if not check_auth(phone, code):
      return 'Auth code is not right, please try again'
    
    file = request.files['file']
    if not file:
      return 'A file must be present'
    if not type(file.filename) in ALLOWED_FILES:
      raise Exception('Invalid filetype ALLOWED:{}'.format(ALLOWED_FILES))
    
    stream = file.stream.read()
    if not stream:
      return 'Problems reading the file'

    filename = '{}-{}'.format(word(), word())
    key = '+52{}.{}'.format(phone, filename)
    
    saved = redis_client.set(key, stream)
    logger.info(key)
    save_type(key, file.filename)
    if saved:
      cache_for_delete(key)
      # send_filename(phone, filename, request.base_url)
      return 'You saved a file with name <h1>{}</h1>. You can retrieve your file at <h2>{}/{}<h2><br><h2>WARN THIS IS A SINGLE USE LINK</h2>'. \
        format(filename, request.base_url, filename)
  
  except Exception as ex:
    logger.error(ex)
    return str(ex)
  return 400


@app.route('/<phone>/<name>', methods=['GET'])
def get(phone, name):
  try:
    key = '+52{}.{}'.format(phone, name)
    content = redis_client.get(key)
    if not content:
      return 'File already served and destroyed'
    filename = get_type(key)
    redis_client.delete(key)
    return send_file(io.BytesIO(content), attachment_filename=filename)
  except Exception as ex:
    logger.error(ex)
    return str(ex)



@app.route('/<phone>', methods=['GET'])
def request_form(phone):
  try:
    resp = auth(phone)
    logger.error(resp)
    if not resp:
      return 'Please provide a cell phone number'

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post action='/{}' enctype=multipart/form-data>
    <input type=file name=file>
    <h2>Enter verification code that we send to your phone</h2>
    <input type=text name=code>
    <input type=submit value=Upload>
    </form>
    '''.format(phone)
  except Exception as ex:
    logger.error(ex)
    return str(ex)


@app.route('/', methods=['GET'])
def home():
  return '''
  <h1>Upload new File</h1>
  
  '''
  
  
