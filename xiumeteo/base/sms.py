from twilio.rest import Client
import os
from authy.api import AuthyApiClient 
import logging

logger = logging.getLogger(__name__)

account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

authy_api = AuthyApiClient(os.getenv('AUTHY_KEY'))

def send_filename(to, key, base_url):
  # resp = client.messages \
  #               .create(
  #                       body="You have a temp file with name '{}'' you can recover it using this url {} . WARN THIS IS SINGLE USE" \
  #                             .format(key, '{}/{}'.format(base_url, key)),
  #                       from_='+15734851574',
  #                       to=to
  #       )

  # return resp.sid 
  pass

def check_phone(phone):
   # resp = client.lookups.phone_numbers('+52{}'.format(phone)).fetch()
   # return resp.phone_number
   pass


def auth(phone):
  logger.error(os.getenv('AUTHY_KEY'))
  resp = authy_api.phones.verification_start(
    phone_number=phone, 
    country_code=52, 
    via='sms')
  if not resp.ok():
    logger.error(resp.content)
  return resp.ok()

def check_auth(phone, code):
  check = authy_api.phones.verification_check(
    phone_number=phone, 
    country_code=52, 
    verification_code=code)

  return check.ok()