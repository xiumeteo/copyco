from redis import Redis
import os
from datetime import datetime as time

class Client():
  def __init__(self):
    self.client = Redis.from_url(os.getenv('REDIS_URL'))

  def cache_for_delete(self, uri):
    self.client.sadd('cache_for_delete', {'key':'uri', 'time':str(time.now())})

client = Client()
  
  
def purge_files():
  # now = time.now()
  # docs = redis_client.smembers()
  # docs_timeout = {}
  # for item in docs:
  # 	doc = json.loads(item.decode('utf-8').replace("'". '"'))
  #   if doc['time']
  pass