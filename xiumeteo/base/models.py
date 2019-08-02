import pyotp
from .redis import client as redis_client
import requests
import random
import logging
import json

logger = logging.getLogger(__name__)

words = requests.get('http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain') \
    .content.decode("utf-8")  \
    .lower() \
    .splitlines()

def word():
  return random.choice(words)

def filetype(filename):
  return filename.rsplit('.', 1)[1].lower()


class StoredItem:
    @staticmethod
    def _file_key(user, filename):
        return '{}.{}'.format(User.user_key(user.phone), filename)

    @staticmethod
    def _file_type_key(file_key):
        return file_key + '.file_type'

    @staticmethod
    def _key(self, file_key):
        return file_key + '.stored_item'

    @staticmethod
    def create(stream, filetype, user):
        filename = '{}-{}'.format(word(), word())
        item = StoredItem(filename, user, stream)
        item.save()
        return item

    @staticmethod
    def load_content(user, filename):
        file_key = StoredItem._file_key(filename)
        stored_item_key = StoredItem._key(file_key)
        
        stored_item_json = redis_client.get_json(stored_item_key)
        if user.key != stored_item_json['user_key']:
            raise Exception('You are not authorized to view this item.')

        stream = redis_client.get_bytes(file_key)
        if not stream:
            raise Exception('File already served and destroyed')
        
        filetype = StoredItem.get_type(stored_item_json['filetype'])
        return StoredItem(filename, filetype, user, stream)

    @staticmethod
    def delete(stored_item_key):
        stored_item_json = redis_client.get_json(stored_item_key)
        redis_client.delete(stored_item_json['file_key'])
        redis_client.delete(stored_item_json['filetype_key'])
        redis_client.delete(stored_item_json['key'])      

    def __init__(self, filename, filetype, user, stream):
        self.stream = stream
        self.file_key = StoredItem._file_key(self.filename)
        self.filename = filename
        self.filetype = self.filetype
        self.filetype_key = StoredItem._file_type_key(self.file_key)
        self.user_key = user.key
        self.key = StoredItem._key(self.file_key)

    def save(self):
        redis_client.save(self.file_key, self.stream)
        redis_client.save(self.filetype_key, self.filetype)
        self.stream = None
        redis_client.save_json(self.key, self.__dict__)
        redis_client.cache_for_deletion(self.key)



class User:
    @staticmethod
    def create(phone):
        hash = pyotp.random_base32()
        user = User(phone, hash)
        user.save()
        return user

    @staticmethod
    def load(phone):
        key = User.user_key(phone)
        json = redis_client.get_json(key)
        if not json:
            return None
        user = User(phone, json['hash'])
        user.files = json['files']
        return user

    @staticmethod
    def user_key(phone):
        return "user.{}".format(phone)

    def __init__(self, phone, hash):
        self.phone = phone
        self.country_code = phone[0:2]
        self.hash = hash
        self.key = User.user_key(self.phone)
        self.files = {}

    @property
    def provision_uri(self):
        return pyotp.TOTP(self.hash).provisioning_uri("{}@copyco".format(self.phone), issuer_name="copyco")

    def save(self):
        redis_client.save_json(self.key, self.__dict__)

    def match(self, code):
        mycode = pyotp.TOTP(self.hash).now()
        return mycode == code

    def load_content(self, name):
        item = StoredItem.load_content(self, name)
        if not item.key in self.files:
            raise Exception('File does not belong to this user')

        self.files.remove(item.key)
        return item
    
    def store(self, stream, file_type):
        item = StoredItem.create(stream, file_type, self)
        self.files.add(item.key)
        self.save()
        return item


