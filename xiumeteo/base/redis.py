from redis import Redis
import os
from datetime import datetime as time
import json

class Client():
  def __init__(self):
    self.client = Redis.from_url(os.getenv('REDIS_URL'))

  def cache_for_delete(self, uri):
    self.client.sadd('cache_for_delete', {"key":"uri", "time":str(time.now())})

  def get_str(self, key):
    data = self.client.get(key)
    if not data:
      return data
    return data.decode('utf-8')

  def get_json(self, key):
    data = self.get_str(key)
    print(data)
    if not data:
      return data
    return json.loads(data)

  def get_bytes(self, key):
    return self.client.get(key)

  def save(self, key, obj):
    return self.client.set(key, obj)

  def save_json(self, key, obj):
    return self.client.set(key, json.dumps(obj))

client = Client()
  
  
def purge_files():
  # now = time.now()
  # docs = redis_client.smembers()
  # docs_timeout = {}
  # for item in docs:
  # 	doc = json.loads(item.decode('utf-8').replace("'". '"'))
  #   if doc['time']
  pass