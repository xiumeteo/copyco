from flask import Flask
import click
from flask_apscheduler import APScheduler
from xiumeteo.base.tasks import cleanup_task
from xiumeteo.api.api import base_api


app = Flask(__name__)
app.register_blueprint(base_api)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.add_job(func=cleanup_task, trigger='interval', hours=6, id='cleanup old files')
scheduler.start()


@app.cli.command("cleanup-old-files")
@click.argument("hours")
def cleanup_old_files(hours=24):
  from xiumeteo.base.redis import client 
  client.delete_all(int(hours))