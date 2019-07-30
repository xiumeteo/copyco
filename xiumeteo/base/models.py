import pyotp
from .redis import client as redis_client
import requests
import random
import logging

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
        json = redis_client.get_object(key)
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

    def generate_provision_uri(self):
        return pyotp.TOTP(self.hash).provisioning_uri("{}@copyco".format(self.phone), issuer_name="copyco")

    def save(self):
        redis_client.save(User.user_key(self.phone), { 'hash':self.hash,
                                                          'country_code': self.country_code })

    def match(self, code):
        mycode = pyotp.TOTP(self.hash).now()
        return mycode == code

    def _file_key(self, filename):
        return '{}.{}'.format(User.user_key(phone), filename)
    
    def store(self, file):
        filename = '{}-{}'.format(word(), word())
        key = self._file_key(filename)
        
        saved = redis_client.set(key, file)
        logger.info('Stored file:{}'.format(key))
        self._save_type(key, file.filename)
        if saved:
            redis_client.cache_for_delete(key)
        return saved, filename

    def load_content(self, name):
        key = self._file_key(name)
        content = redis_client.get(key)
        if not content:
            return 'File already served and destroyed'
        filename = get_type(key)
        return filename, content


    def _save_type(uri, filename):
        key = uri + '.filename'
        return redis_client.set(key, filename)

    def get_type(uri):
        return redis_client.get(uri + '.filename').decode('utf-8')

def type(filename):
  return filename.rsplit('.', 1)[1].lower()
