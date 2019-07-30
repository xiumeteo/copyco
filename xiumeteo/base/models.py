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
        return User(phone, json['hash'])

    @staticmethod
    def user_key(phone):
        return "user.{}".format(phone)

    def __init__(self, phone, hash):
        self.phone = phone
        self.country_code = phone[0:2]
        self.hash = hash

    @property
    def provision_uri(self):
        return pyotp.TOTP(self.hash).provisioning_uri("{}@copyco".format(self.phone), issuer_name="copyco")

    def save(self):
        redis_client.save_json(User.user_key(self.phone), { "hash":self.hash,
                                                          "country_code": self.country_code })

    def match(self, code):
        mycode = pyotp.TOTP(self.hash).now()
        return mycode == code

    def _file_key(self, filename):
        return '{}.{}'.format(User.user_key(self.phone), filename)
    
    def store(self, file, file_type):
        filename = '{}-{}'.format(word(), word())
        key = self._file_key(filename)
        
        saved = redis_client.save(key, file)
        logger.info('Stored file:{}'.format(key))
        self._save_type(key, file_type)
        if saved:
            redis_client.cache_for_delete(key)
        return saved, filename

    def load_content(self, name):
        key = self._file_key(name)
        content = redis_client.get_bytes(key)
        if not content:
            raise Exception('File already served and destroyed')
        filename = self.get_type(key)
        return filename, content

    def _save_type(self, uri, filename):
        key = uri + '.filename'
        return redis_client.save(key, filename)

    def get_type(self, uri):
        return redis_client.get_str(uri + '.filename')

def filetype(filename):
  return filename.rsplit('.', 1)[1].lower()
