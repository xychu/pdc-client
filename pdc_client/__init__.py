# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import itertools
import json
import sys

import beanbag
import requests
import requests_kerberos
import warnings
from os.path import expanduser, isfile

from pdc_client import monkey_patch

monkey_patch.monkey_patch_kerberos()

__version__ = '0.2.0'

GLOBAL_CONFIG_FILE = '/etc/pdc/client_config.json'
USER_SPECIFIC_CONFIG_FILE = expanduser('~/.config/pdc/client_config.json')
CONFIG_URL_KEY_NAME = 'host'
CONFIG_INSECURE_KEY_NAME = 'insecure'
CONFIG_DEVELOP_KEY_NAME = 'develop'
CONFIG_TOKEN_KEY_NAME = 'token'


def _read_file(file_path):
    data = {}
    if isfile(file_path):
        with open(file_path, 'r') as config_file:
            data = json.load(config_file)
    return data


def read_config_file(server_alias):
    result = _read_file(GLOBAL_CONFIG_FILE).get(server_alias, {})
    result.update(_read_file(USER_SPECIFIC_CONFIG_FILE).get(server_alias, {}))
    return result


def get_paged(res, **kwargs):
    """
    This call is equivalent to ``res(**kwargs)``, only it retrieves all pages
    and returns the results joined into a single iterable. The advantage over
    retrieving everything at once is that the result can be consumed
    immediately.

    :param res:     what resource to connect to
    :param kwargs:  filters to be used

    ::

        # Example: Iterate over all active releases
        for release in get_paged(client['releases']._, active=True):
            ...
    """
    def worker():
        kwargs['page'] = 1
        while True:
            response = res(**kwargs)
            yield response['results']
            if response['next']:
                kwargs['page'] += 1
            else:
                break
    return itertools.chain.from_iterable(worker())


class PDCClient(object):
    """BeanBag wrapper specialized for PDC access.

    This class wraps general BeanBag.v1 objects, but provides easy-to-use
    interface that can use configuration files for specifying server
    connections. The authentication token is automatically retrieved (if
    needed).
    """
    def __init__(self, server, token=None, develop=False, insecure=False):
        """Create new client instance.

        Once the class is instantiated, use it as you would use a regular
        BeanBag object. Please see its documentation to see how to use this
        class to perform requests.

        :param server:     server API url or server name from configuration
        :paramtype server: string
        """
        if not server:
            raise TypeError('Server must be specified')
        self.session = requests.Session()
        config = read_config_file(server)
        url = server

        if config:
            try:
                url = config[CONFIG_URL_KEY_NAME]
            except KeyError:
                print "'%s' must be specified in configuration file." % CONFIG_URL_KEY_NAME
                sys.exit(1)
            insecure = config.get(CONFIG_INSECURE_KEY_NAME, insecure)
            develop = config.get(CONFIG_DEVELOP_KEY_NAME, develop)
            token = config.get(CONFIG_TOKEN_KEY_NAME, token)

        if not develop:
            # For local environment, we don't need to require a token,
            # just access API directly.
            # REQUIRED, OPTIONAL, DISABLED
            self.session.auth = requests_kerberos.HTTPKerberosAuth(
                mutual_authentication=requests_kerberos.DISABLED)

        if insecure:
            # turn off for servers with insecure certificates
            self.session.verify = False
            # turn off warnings about making insecure calls
            if requests.__version__ < '2.4.0':
                print "Requests version is too old, please upgrade to 2.4.0 or latest."
                # disable all warnings, it had better to upgrade requests.
                warnings.filterwarnings("ignore")
            else:
                requests.packages.urllib3.disable_warnings()

        self.client = beanbag.BeanBag(url, session=self.session)

        if not develop:
            # For develop environment, we don't need to require a token
            if not token:
                token = self.obtain_token()
            self.session.headers["Authorization"] = "Token %s" % token

    def obtain_token(self):
        """
        Try to obtain token from all end-points that were ever used to serve the
        token. If the request returns 404 NOT FOUND, retry with older version of
        the URL.
        """
        token_end_points = ('token/obtain',
                            'obtain-token',
                            'obtain_token')
        for end_point in token_end_points:
            try:
                return self.auth[end_point]._()['token']
            except beanbag.BeanBagException, e:
                if e.response.status_code != 404:
                    raise
        raise Exception('Could not obtain token from any known URL.')

    def __call__(self, *args, **kwargs):
        return self.client(*args, **kwargs)

    def __getattr__(self, name):
        return self.client.__getattr__(name)

    def __getitem__(self, *args, **kwargs):
        return self.client.__getitem__(*args, **kwargs)

    def set_comment(self, comment):
        """Set PDC Change comment to be stored on the server.

        Once you set the comment, it will be sent in all subsequent requests.

        :param comment:     what comment to send to the server
        :paramtype comment: string
        """
        self.session.headers["PDC-Change-Comment"] = comment
