from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six
import time

from pytz import utc
from sqlalchemy import Column, Integer, String

from qbittorrentapi import Client
from qbittorrentapi.exceptions import NotFound404Error

from monitorrent.db import Base, DBSession
from monitorrent.plugin_managers import register_plugin
from monitorrent.utils.bittorrent_ex import Torrent
from datetime import datetime


class QBittorrentCredentials(Base):
    __tablename__ = "qbittorrent_credentials"

    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)


class QBittorrentClientPlugin(object):
    name = "qbittorrent"
    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Host',
            'model': 'host',
            'flex': 80
        }, {
            'type': 'text',
            'label': 'Port',
            'model': 'port',
            'flex': 20
        }]
    }, {
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Username',
            'model': 'username',
            'flex': 50
        }, {
            'type': 'password',
            'label': 'Password',
            'model': 'password',
            'flex': 50
        }]
    }]
    DEFAULT_PORT = 8080
    SUPPORTED_FIELDS = ['download_dir', 'download_category']
    ADDRESS_FORMAT = "{0}:{1}"
    _client = None

    def get_client(self):
        if not self._client:
            self._client = self._get_client()
        return self._client

    def _get_client(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()

            if not cred:
                return False

            if not cred.port:
                cred.port = self.DEFAULT_PORT

            address = self.ADDRESS_FORMAT.format(cred.host, cred.port)

            client = Client(host=address, username=cred.username, password=cred.password)
            client.app_version()
            return QBittorrentClientPlugin._decorate_post(client)

    def get_settings(self):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                return None
            return {'host': cred.host, 'port': cred.port, 'username': cred.username}

    def set_settings(self, settings):
        with DBSession() as db:
            cred = db.query(QBittorrentCredentials).first()
            if not cred:
                cred = QBittorrentCredentials()
                db.add(cred)
            cred.host = settings['host']
            cred.port = settings.get('port', None)
            cred.username = settings.get('username', None)
            cred.password = settings.get('password', None)

    def check_connection(self):
        try:
            client = self.get_client()
            client.app_version()
            return True
        except Exception as inst:
            return False

    def find_torrent(self, torrent_hash):
        client = self.get_client()
        if not client:
            return False

        try:
            torrent = client.torrents_properties(torrent_hash.lower())
            result_date = datetime.fromtimestamp(torrent.addition_date, utc)
            return {
                "name": torrent.save_path,
                "date_added": result_date
            }
        except NotFound404Error:
            return False

    def get_download_dir(self):
        client = self.get_client()
        if not client:
            return None

        result = client.app_default_save_path()
        return six.text_type(result)

    def get_download_category(self):
        client = self.get_client()
        if not client:
            return None

        categories = client.torrents_categories()
        result = ['']
        result.extend(categories.keys())
        return result

    def add_torrent(self, torrent_content, torrent_settings):
        """
        :type torrent_settings: clients.TopicSettings | None
        """
        client = self.get_client()
        if not client:
            return False

        savepath = None
        category = None
        auto_tmm = None
        if torrent_settings is not None:
            if torrent_settings.download_dir is not None:
                savepath = torrent_settings.download_dir
                auto_tmm = False
            if torrent_settings.download_category is not None:
                category = torrent_settings.download_category

        res = client.torrents_add(save_path=savepath, category=category, use_auto_torrent_management=auto_tmm, torrent_contents=[('file.torrent', torrent_content)])
        if 'Ok' in res:
            torrent = Torrent(torrent_content)
            torrent_hash = torrent.info_hash
            repeat_cnt = 30
            while True:
                found = self.find_torrent(torrent_hash)
                if found and found["date_added"]:
                    return True
                if repeat_cnt == 0:
                    return False
                time.sleep(1)
                repeat_cnt -= 1

        return False

    def remove_torrent(self, torrent_hash):
        client = self.get_client()
        if not client:
            return False

        client.torrents_delete(hashes=[torrent_hash.lower()])
        return True

    @staticmethod
    def _decorate_post(client):
        def _post_decorator(func):
            def _post_wrapper(*args, **kwargs):
                if 'torrent_contents' in kwargs:
                    kwargs['files'] = kwargs['torrent_contents']
                    del kwargs['torrent_contents']
                return func(*args, **kwargs)
            return _post_wrapper

        client._post = _post_decorator(client._post)
        return client


register_plugin('client', 'qbittorrent', QBittorrentClientPlugin())
