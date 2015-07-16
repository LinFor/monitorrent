import os

import cherrypy
from db import init_db_engine, create_db
from plugin_managers import load_plugins, TrackersManager, ClientsManager

engine = init_db_engine("sqlite:///monitorrent.db", True)
load_plugins()
create_db(engine)

tracker_manager = TrackersManager()
clients_manager = ClientsManager()


class App(object):
    def __init__(self):
        super(App, self).__init__()
        self.api = Api()

    @cherrypy.expose
    def index(self):
        # return file('./static/index.html')
        raise cherrypy.HTTPRedirect("/static/index.html")


class Api(object):
    def __init__(self):
        super(Api, self).__init__()
        self.torrents = TorrentsApi()
        self.clients = ClientsApi()

    @cherrypy.expose
    def parse(self, url):
        name = tracker_manager.parse_url(url)
        if name: return name
        raise cherrypy.HTTPError(404, "Can't parse url %s" % url)

    @cherrypy.expose
    def check_client(self, client):
        cherrypy.response.status = 200 if clients_manager.check_connection(client) else 500


class TorrentsApi(object):
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self):
        return tracker_manager.get_watching_torrents()

    def DELETE(self, url):
        cherrypy.response.status = 204 if tracker_manager.remove_watch(url) else 404

    @cherrypy.tools.json_in()
    def POST(self):
        result = cherrypy.request.json
        if not result or 'url' not in result:
            raise cherrypy.HTTPError(404, 'missing required url parameter in body')
        cherrypy.response.status = 201 if tracker_manager.add_watch(result['url']) else 400


class ClientsApi(object):
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self, client):
        return clients_manager.get_settings(client)

    @cherrypy.tools.json_in()
    def PUT(self, client):
        settings = cherrypy.request.json
        clients_manager.set_settings(client, settings)
        cherrypy.response.status = 204


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        },
        '/api/torrents': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
        '/api/clients': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
    }

    cherrypy.quickstart(App(), config=conf)
