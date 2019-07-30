from flask import Flask, request, send_file, flash, redirect, url_for
from xiumeteo.base.redis import client as redis_client
from xiumeteo.base.models import User, filetype

from xiumeteo.base.sms import send_filename, check_phone, check_auth, auth
import requests
import random
import logging
import io

app = Flask(__name__)

ALLOWED_FILES = {'jpeg', 'jpg', 'gif', 'pdf', 'doc', 'docx', 'xsx', 'png', 'txt', 'csv'}


@app.route('/<phone>', methods=['GET'])
def add_file(phone):
  if not User.load(phone):
    return '<h1>Sorry user not found.</h1>'

  return '''<!doctype html>
    <title>Submit a file</title>
    <h1>Submit a file</h1>
    <form method=post action='/{}' enctype=multipart/form-data>
    <input type=file name=file>
    <h2>Enter verification code on ur auth app</h2>
    <input type=text name=code>
    <input type=submit value=Upload>
    </form>
    '''.format(phone)


@app.route('/<phone>', methods=['POST'])
def put_file(phone):
  try:
    code = request.form['code']
    user = User.load(phone)
    if not user:
      return '<h1>Sorry user not found.</h1>'

    if not user.match(code):
      return '<h1>Code is wrong.</h1>'
    
    file = request.files['file']
    if not file:
      return 'A file must be present'
    
    file_type = filetype(file.filename)
    if not file_type in ALLOWED_FILES:
      raise Exception('Invalid filetype ALLOWED:{}'.format(ALLOWED_FILES))
    
    stream = file.stream.read()
    if not stream:
      return 'Problems reading the file'

    saved, filename = user.store(stream, file_type)
    if not saved:
      return 'Problems while storing the file.'

      # send_filename(phone, filename, request.base_url)
    return '''You saved a file with name <h1>{}</h1>. 
              You can retrieve your file at 
            <h2>{}/{}<h2>
            <br><h2>WARN THIS IS A SINGLE USE LINK</h2>'''. \
        format(filename, request.base_url, filename)
  
  except Exception as ex:
    app.logger.error(ex)
    return str(ex)
  return 400


@app.route('/<phone>/<name>', methods=['GET'])
def get_file(phone, code, name):
  try:
    user = User.load(phone)
    if not user:
      return '<h1>Sorry user not found.</h1>'

    # if not user.match(code):
    #   return 'Auth code is not right, please try again'

    filename, content = user.load_content(name)
    print(filename)
    return send_file(io.BytesIO(content), attachment_filename='{}.{}'.format(name, filename))
  except Exception as ex:
    app.logger.error(ex)
    return str(ex)


@app.route('/signup/<phone>', methods=['POST'])
def signup_check_code(phone):
  try:
    code = request.form['code']
    if not check_auth(phone, code):
      return 'Auth code is not right, please try again, go to {}'.format(url_for('signup_init'))
    
    user = User.create(phone)
    return redirect("https://www.qrcoder.co.uk/api/v1/?text={}".format(user.provision_uri))
  except Exception as ex:
    app.logger.error(ex)
    return str(ex)


@app.route('/signup', methods=['POST'])
def signup_add_phone():
  try:
    phone = request.form.get('phone')
    app.logger.info('Attempting to sign up {}'.format(phone))
    if not phone:
      return 'No phone is present, please change that.'
    
    if User.load(phone):
      app.logger.error('Client with phone number attempted signup {}'.format(phone))
      return 'That client is already here.'

    resp = auth(phone) 
    app.logger.info(resp)
    if not resp:
      return 'Please provide a valid phone number'

    return '''
    <!doctype html>
    <title>You are almost done!</title>
    <h1>You are almost done!</h1>
    <form method=post action='/signup/{}' enctype=form-data>
    <h2>Enter verification code that we send to your phone</h2>
    <input type=text name=code>
    <input type=submit value=Upload>
    </form>
    '''.format(phone)
  except Exception as ex:
    app.logger.error(ex)
    return str(ex)


@app.route('/init', methods=['GET'])
def signup_init():
  return '''
  <h1>Put ur phone using the international format</h1>
  <form method=post action='/signup' >
    Telephone
    <input type=tel name=phone>
    <input type=submit value=Sign up>
  </form>
  '''

@app.route('/', methods=['GET'])
def home():
  base = request.base_url
  return '''
  <h1>Welcome to copyco</h1>
  <ol>
    <li>Go to {}/init and fill the details</li>
    <li>Enter the verification code</li>
    <li>Scan the qr code using Google Auth, Msoft Auth or similar apps</li>
  </ol>
  <h2>Once ur account is setup, you can add files using</h2>
  <ol>
    <li>Go to {}/phone_number and upload ur files!</li>
    <li>Go to {}/phone_number/passphrase </li>
    <li>Download ur files</li>
  </ol>
  <h2>The file will be destroyed after your download</h2>
  <h2>The file will be destroyed after a day of submission</h2>
  '''.format(base, base, base)
  
  
