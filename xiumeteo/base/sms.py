from twilio.rest import Client
import os

account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

def send_filename(to, key, base_url):
  resp = client.messages \
                .create(
                        body="You have a temp file with name '{}'' you can recover it using this url {} . WARN THIS IS SINGLE USE" \
                              .format(key, '{}/{}'.format(base_url, key)),
                        from_='+15734851574',
                        to=to
        )

  return resp.sid 

def check_phone(phone):
   resp = client.lookups.phone_numbers('+52{}'.format(phone)).fetch()
   return resp.phone_number