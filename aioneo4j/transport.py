import asyncio
import collections
import json
import logging

import aiohttp
import async_timeout
from aiohttp import ClientError

from . import errors


logger = logging.getLogger("aioneo4j.transport")


class Transport:
    r"""A transport object for a Neo4j client, which performs all the heavy lifting requests on the backend for the client

    Parameters
    -----------
    url: :class:`str`
        The base URL of the database for us to connect to
    auth: :class:`tuple`
        The (username, password) pair for us to authenticate with
    database: :class:`str`
        The name of the database we'll be connecting to
    request_timeout: :class:`float`
        The timeout to be used when performing a request
    """

    _auth = None

    def __init__(self, url, auth, database, encoder=json.dumps, decoder=json.loads, encoder_errors=(TypeError, ValueError), decoder_errors=(TypeError, ValueError), request_timeout=..., session=None, maxsize=20, use_dns_cache=False, *, loop ):
        self.loop = loop
        self.url = url
        self.database = database
        self.auth = auth
        self.encoder = encoder
        self.decoder = decoder
        self.encoder_errors = encoder_errors
        self.decoder_errors = decoder_errors
        self.request_timeout = request_timeout

        self.session = session
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    limit=maxsize,
                    use_dns_cache=use_dns_cache,
                    loop=self.loop,
                ),
            )

    def get_auth(self):
        return self._auth

    def set_auth(self, auth):
        if auth is not None:
            if isinstance(auth, str):
                username, password = auth.split(':')
            elif isinstance(auth, collections.Sequence):
                username, password = auth
            auth = aiohttp.BasicAuth(
                login=username,
                password=password,
            )
        self._auth = auth

    auth = property(get_auth, set_auth)
    del get_auth, set_auth

    @property
    def headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json; charset=UTF-8',
        }

    async def _perform_request(self, method, url, params=None, data=None):

        response = None

        try:
            logger.debug(f"Performing {method.upper()} {url} ({params}) with data {data} and auth {self.auth}")
            response = await self.session.request(
                method,
                url,
                params=params,
                data=data,
                headers=self.headers,
                auth=self.auth,
                timeout=None,
            )

            text = await response.text()

            if not (200 <= response.status <= 300):
                extra = None

                try:
                    extra = self.decoder(text)
                except self.decoder_errors:
                    pass

                raise errors.ClientError(response.status, extra or text)

            return response.status, response.headers, text
        except ClientError as exc:
            logger.error(exc)
            raise errors.TransportError from exc
        finally:
            if response is not None:
                await response.release()

    async def perform_request(self, method:str, path:str, params:dict=None, data:dict=None, request_timeout:float=...):
        r"""Perform a web request at the database

        Parameters
        -----------
        method: :class:`str`
            The method to be used when performing the request
        path: :class:`str`
            The endpoint you want to ping the request to
        params: :class:`dict`
            The URL parameters to use
        data: :class:`dict`
            The JSON data to send, if any
        request_timeout: :class:`float`
            The timeout you want to use when performing the request

        Returns
        --------
        The resulting data as a (status_code, headers, data) triplet
        """

        # Encode the data
        if data is not None:
            logger.debug(f"Encoding data {data}")
            if not isinstance(data, (str, bytes)):
                try:
                    data = self.encoder(data)
                except self.encoder_errors as exc:
                    raise errors.SerializationError from exc

            if not isinstance(data, bytes):
                data = data.encode('utf-8')

        # Work out our URL
        _url = self.url / f'db/{self.database}/{path}'
        logger.debug(f"Sending request to {_url} with data {data}")
        _coro = self._perform_request(method, _url, params=params, data=data)

        # Work out our timeout
        _request_timeout = request_timeout
        if request_timeout is ...:
            _request_timeout = self.request_timeout
        if _request_timeout is ...:
            _request_timeout = None

        # Perform the request
        try:
            with async_timeout.timeout(_request_timeout, loop=self.loop):
                status, headers, data = await _coro
        except asyncio.TimeoutError:
            raise errors.TimeoutError

        # If we got data, let's decode that
        if data:
            try:
                data = self.decoder(data)
            except self.decoder_errors as exc:
                raise errors.SerializationError from exc

        # There's an error in the data? Raise that
        if isinstance(data, collections.Mapping) and data.get('errors'):
            raise errors.ClientError(data['errors'])

        # Return the status code and the data given
        return status, data

    async def close(self):
        await self.session.close()
