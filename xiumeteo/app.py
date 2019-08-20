from flask import Flask
from flask_apscheduler import APScheduler
from xiumeteo.base.tasks import cleanup_task
from xiumeteo.api.api import base_api



def create_app():
  app = Flask(__name__)
  app.register_blueprint(base_api)
  scheduler = APScheduler()
  scheduler.init_app(app)
  scheduler.add_job(func=cleanup_task, trigger='interval', hours=6, id='cleanup old files')
  scheduler.start()
  return app


