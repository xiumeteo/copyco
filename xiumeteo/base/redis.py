from redis import Redis
import os
from datetime import datetime as time
import json
import logging

logger = logging.getLogger(__name__)


class TestStore():
    def __init__(self):
        self.store = dict()

    def sadd(self, key, data):
        if not self.get(key):
            self.store[key] = set(data)
        else:
            self.get(key).add(data)

    def smembers(self, key):
        return self.get(key)

    def srem(self, key, item):
        self.get(key).remove(item)

    def delete(self, key):
        del self.store[key]

    def get(self, key):
        return self.store[key]

    def set(self, key, data):
        self.store[key] = data


class Client():
    def __init__(self, is_test=False):
        if not is_test:
            self.client = Redis.from_url(os.getenv('REDIS_URL'))
        else:
            self.client = TestStore()

    def cache_for_deletion(self, stored_item_key):
        data = json.dumps({"key": stored_item_key, "time": str(time.now())})
        self.client.sadd('cache_for_delete', data)

    def to_date(self, str_date):
        return time.strptime(str_date, "%Y-%m-%d %H:%M:%S.%f")

    def delete(self, key):
        return self.client.delete(key)

    def delete_all(self, hours=24):
        items = self.client.smembers('cache_for_delete')
        logger.info('Found items in the cache : {}'.format(items))
        from xiumeteo.base.models import StoredItem
        for item in items:
            data = item.decode('utf-8')
            stored_item = json.loads(data)
            stored_item_ts = self.to_date(stored_item['time'])
            import datetime
            if time.now() - stored_item_ts >= datetime.timedelta(hours=hours):
                logger.info('Removing {} '.format(item))
                self.client.srem('cache_for_delete', item)
                stored_item_key = stored_item['key']
                StoredItem.delete(stored_item_key)

    def get_str(self, key):
        data = self.client.get(key)
        if not data:
            return data
        return data.decode('utf-8')

    def get_json(self, key):
        data = self.get_str(key)
        logger.info(data)
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
