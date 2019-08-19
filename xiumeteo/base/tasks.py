from xiumeteo.base.redis import client as redis_client

def cleanup_task():
  print("Running")
  redis_client.delete_all()
