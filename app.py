from flask import Flask, request, send_file, flash, redirect, url_for, render_template
import click
from xiumeteo.base.redis import client as redis_client
from xiumeteo.base.models import User, filetype

from xiumeteo.base.sms import send_filename, check_phone, check_auth, auth
import requests
import random
import logging
import io
from flask_apscheduler import APScheduler


def cleanup_task():
  print("Running")
  redis_client.delete_all()


app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.add_job(func=cleanup_task, trigger='interval', hours=6, id='cleanup old files')
scheduler.start()
app.run()

@app.cli.command("cleanup-old-files")
@click.argument("hours")
def cleanup_old_files(hours=24):
  print('asdljfsadjf')
  redis_client.delete_all(int(hours))

ALLOWED_FILES = {'jpeg', 'jpg', 'gif', 'pdf', 'doc', 'docx', 'xsx', 'png', 'txt', 'csv'}

def user_not_found():
  return render_template('user_not_found.html')

def invalid_file():
  return render_template('invalid_file.html', filetype=ALLOWED_FILES)

def problems_with_file():
  return render_template('problem_with_file.html')

@app.route('/<phone>', methods=['GET'])
def add_file(phone):
  if not User.load(phone):
    return user_not_found()

  return render_template('add_file_form.html', phone=phone)


@app.route('/<phone>', methods=['POST'])
def put_file(phone):
  try:
    code = request.form['code']
    user = User.load(phone)
    if not user:
      return user_not_found()

    if not user.match(code):
      return render_template('invalid_code.html')
    
    file = request.files['file']
    if not file:
      return invalid_file()
    
    file_type = filetype(file.filename)
    if not file_type in ALLOWED_FILES:
      return invalid_file()
    
    stream = file.stream.read()
    if not stream:
      return problems_with_file()

    item = user.store(stream, file_type)
    if not item:
      return problems_with_file()

    return render_template('save_file_success.html', filename=item.filename, base=request.base_url)
  
  except Exception as ex:
    app.logger.error(ex)
    return str(ex)
  return 400


@app.route('/<phone>/<name>', methods=['GET'])
def get_file(phone, name):
  try:
    user = User.load(phone)
    if not user:
      return user_not_found()

    stored_item = user.load_content(name)
    print(stored_item.filename)
    return send_file(io.BytesIO(stored_item.stream), attachment_filename='{}.{}'.format(name, stored_item.filetype))
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

    return render_template('signup_add_phone.html', phone=phone)
  except Exception as ex:
    app.logger.error(ex)
    return str(ex)


@app.route('/init', methods=['GET'])
def signup_init():
  return render_template('signup_init.html')

@app.route('/', methods=['GET'])
def home():
  base = request.base_url
  return render_template('index.html', base=base)


