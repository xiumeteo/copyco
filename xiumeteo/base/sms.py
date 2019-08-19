from twilio.rest import Client
import os
from authy.api import AuthyApiClient 
import logging

logger = logging.getLogger(__name__)

account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

authy_api = AuthyApiClient(os.getenv('AUTHY_KEY'))


def auth(phone):
  resp = authy_api.phones.verification_start(
    phone_number=phone, 
    country_code=phone[0:2], 
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