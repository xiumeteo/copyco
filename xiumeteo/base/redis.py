from redis import Redis
import os
from datetime import datetime as time
import json

class Client():
  def __init__(self):
    self.client = Redis.from_url(os.getenv('REDIS_URL'))

  def cache_for_deletion(self, stored_item_key):
    data = json.dumps({"key":stored_item_key, "time":str(time.now())})
    self.client.sadd('cache_for_delete', data)

  def to_date(self, str_date):
    pass

  def delete_all(self):
    items = self.client.smembers('cache_for_delete')
    for item in items:
      data = item.decode('utf-8')
      stored_item = json.loads(data)
      stored_item_ts = to_date(stored_item['time'])
      if stored_item_ts >= time.timedelta(days=1):
        self.client.srem('cache_for_delete', item)
        stored_item_key = stored_item['key']
        from xiumeteo.base.models import StoredItem
        StoredItem.delete(stored_item_key)    

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