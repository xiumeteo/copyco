from flask import Flask, request
from xiumeteo.base.redis import redis_client
from werkzeug.utils import secure_filename
import requests
import random
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

words = requests.get('http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain').content.decode("utf-8").lower().splitlines()

def word():
  return random.choice(words)

@app.route('/put/<phone>', methods=['POST'])
def put(phone):
  file = request.files['file']
  logger.error(file)
  if not file:
    return 404
  filename = '{}-{}'.format(word(), word())
  stream = file.stream.read()
  logger.error(filename) 
  logger.error(stream) 
  if not stream:
    return 400
  return '{}, {}'.format(redis_client.set('{}.{}'.format(phone, filename), stream), filename)

@app.route('/save', methods=['GET'])
def save():
  return '''
  <!doctype html>
  <title>Upload new File</title>
  <h1>Upload new File</h1>
  <form method=post action='/put/9999471847' enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
  </form>
  '''
  
  
