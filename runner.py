from xiumeteo.app import create_app
import click

app = create_app()

if __name__ == "__main__":
    app.run()

@app.cli.command("cleanup-old-files")
@click.argument("hours")
def cleanup_old_files(hours=24):
  from xiumeteo.base.redis import client 
  client.delete_all(int(hours))