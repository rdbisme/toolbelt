# -*- coding: utf-8 -*-
"""The implementation of the SocketOptionsAdapter."""
import socket

import requests
from requests import adapters
from requests.packages.urllib3 import connection
from requests.packages.urllib3 import poolmanager

_SENTINEL = object()


class SocketOptionsAdapter(adapters.HTTPAdapter):
    """An adapter for requests that allows users to specify socket options.

    Since version 2.4.0 of requests, it is possible to specify a custom list
    of socket options that need to be set before establishing the connection.

    Example usage::

        >>> import socket
        >>> import requests
        >>> from requests_toolbelt.adapters import socket_options
        >>> s = requests.Session()
        >>> opts = [(socket.IPROTO_TCP, socket.TCP_NODELAY, 0)]
        >>> adapter = socket_options.SocketOptionsAdapter(socket_options=opts)
        >>> s.mount('http://', adapter)

    You can also take advantage of the list of default options on this class
    to keep using the original options in addition to your custom options. In
    that case, ``opts`` might look like::

        >>> opts = socket_options.SocketOptionsAdapter.default_options + opts

    """

    default_options = connection.HTTPConnection.default_socket_options

    def __init__(self, **kwargs):
        self.socket_options = kwargs.pop('socket_options',
                                         self.default_options)

        super(SocketOptionsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        if requests.__build__ >= 0x020400:
            self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                socket_options=self.socket_options
            )
        else:
            super(SocketOptionsAdapter, self).init_poolmanager(
                connections, maxsize, block
            )


class TCPKeepAliveAdapter(SocketOptionsAdapter):
    """An adapter for requests that turns on TCP Keep-Alive by default.

    The adapter sets 4 socket options:

    - ``SOL_SOCKET`` ``SO_KEEPALIVE`` - This turns on TCP Keep-Alive
    - ``IPROTO_TCP`` ``TCP_KEEPIDLE`` 60 - Sets the keep alive time
    - ``IPROTO_TCP`` ``TCP_KEEPINTVL`` 20 - Sets the keep alive interval
    - ``IPROTO_TCP`` ``TCP_KEEPCNT`` 5 - Sets the number of keep alive probes

    The latter three can be overridden by keyword arguments (respectively):

    - ``idle``
    - ``interval``
    - ``count``

    You can use this adapter like so::

       >>> from requests_toolbelt.adapters import socket_options
       >>> tcp = socket_options.TCPKeepAliveAdapter(idle=120, interval=10)
       >>> s = requests.Session()
       >>> s.mount('http://', tcp)

    """

    def __init__(self, **kwargs):
        idle = kwargs.pop('idle', 60)
        interval = kwargs.pop('interval', 20)
        count = kwargs.pop('count', 5)
        socket_options = SocketOptionsAdapter.default_options + [
            (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            (socket.IPROTO_TCP, socket.TCP_KEEPIDLE, idle),
            (socket.IPROTO_TCP, socket.TCP_KEEPINTVL, interval),
            (socket.IPROTO_TCP, socket.TCP_KEEPCNT, count),
        ]
        super(TCPKeepAliveAdapter, self).__init__(
            socket_options=socket_options, **kwargs
        )
