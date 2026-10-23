import os
import click
from flask import Flask, send_from_directory
from flask import current_app as app
from flask_restx import Api, Resource
import gevent
import signal
from gevent.pywsgi import WSGIServer

from dfmt import PACKAGE_ROOT
from .api import namespace

def create_app():
    """
    Create api singleton instance, intialize it and return it.
    """
    app = Flask(__name__, instance_path=PACKAGE_ROOT)
    app.url_map.strict_slashes = False
    app.config['JSON_SORT_KEYS'] = False
    app.config['ERROR_404_HELP'] = False
    app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
    authorizations = { 
        'Authorization': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        },
    }
    api = Api(
        title='DMFT Api',
        version='1.0',
        description='An api used to create hash databases of disk images and query files on those images',
        authorizations=authorizations, 
        security='Authorization'
    )
    api.add_namespace(namespace)
    api.init_app(app)
    return app

@click.group()
def cli():
    pass

@cli.command()
@click.option("--host", default="0.0.0.0", help="The interface to bind to.")
@click.option("--port", default=8000, help="The port to bind to.")
@click.option("--api-key", required=True, help="The api key to be used to authenticate all requests.")
def start(host, port, api_key):
    """
    Create the api and serve it on the given host and port. Wait for shutdown.
    """
    app = create_app()
    app.config["API_KEY"] = api_key
    server = WSGIServer((host, port), app)
    def shutdown():
        click.echo('Terminating...')
        server.stop()
        exit(signal.SIGINT)
    gevent.signal(signal.SIGINT, shutdown)
    click.echo(f"Starting DFMT Api on http://{host}:{port}...")
    click.echo("Press Ctrl+C to terminate")
    server.serve_forever()