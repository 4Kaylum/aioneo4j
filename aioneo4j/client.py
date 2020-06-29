import asyncio
import collections
import typing

from yarl import URL

from .transport import Transport


class Client(object):
    r"""A Neo4j client object, used to interface with your Neo4j database

    Parameters
    -----------
    url: :class:`str`
        The HTTP url of your database.
    auth: Optional[:class:`tuple`]
        A pair of (username, password) used to authenticate with your database.
        Will be interpreted from the URL if you provided auth information there.
    transport: Optional[:class:`Transport`]
        The aiohttp transport method for actually performing given requests.
    request_timeout: Optional[:class:`float`]
        How long a request should wait to process before timing out.
    """

    def __init__(self, url:str='http://127.0.0.1:7474/', auth:typing.Tuple[str]=None, transport:Transport=Transport, request_timeout:float=..., *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        url = URL(url)
        if url.user and url.password:
            auth = url.user, url.password
            url = url.with_user(None)
            url = url.with_password(None)  # TODO: not sure is it needed
        self.transport = transport(
            url=url,
            auth=auth,
            request_timeout=request_timeout,
            loop=self.loop,
        )

    def get_auth(self):
        return self.transport.auth

    def set_auth(self, auth):
        self.transport.auth = auth

    auth = property(get_auth, set_auth)

    del get_auth, set_auth

    async def data(self, path='db/data', request_timeout=...):
        r"""Get all the data from the database"""

        _, data = await self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )
        return data

    async def cypher(self, query:str, path:str='db/data/cypher', request_timeout:float=..., **params):
        r"""Run a cypher on the database

        Parameters
        -----------
        query: :class:`str`
            The query you want to run
        kwargs:
            Any of the kwargs you give the cypher will be used as input variables
        """

        # If the query is a dict, we'll assume they gave the actual POST data and go from there
        if isinstance(query, collections.Mapping):
            assert not params
            request = query
        else:
            request = {'query': query}
            if params:
                request['params'] = params

        _, data = await self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )
        return data

    async def transaction_commit(self, *statements, path='db/data/transaction/commit', request_timeout=...):
        r"""Commit a transaction"""

        # Parse out the multiple statements given
        if len(statements) == 1 and isinstance(statements[0], collections.Mapping) and 'statements' in statements[0]:
            request = statements[0]
        else:
            request = {'statements': []}

            for statement in statements:
                if not isinstance(statement, collections.Mapping):
                    statement = {'statement': statement}
                else:
                    if 'statement' not in statement:
                        raise ValueError

                request['statements'].append(statement)

        _, data = await self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )
        return data

    async def indexes(self, path='db/data/schema/index', request_timeout=...):
        _, data = await self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )
        return data

    async def constraints(self, path='db/data/schema/constraint', request_timeout=...):
        _, data = await self.transport.perform_request(
            'GET',
            path,
            request_timeout=request_timeout,
        )
        return data

    async def user_password(self, password, username='neo4j', path='user/{username}/password', set_auth=False, request_timeout=...):
        path = path.format(username=username,)
        request = {'password': password}
        _, data = await self.transport.perform_request(
            'POST',
            path,
            data=request,
            request_timeout=request_timeout,
        )
        if set_auth:
            auth = username, password
            self.auth = auth
        return data

    async def close(self):
        await self.transport.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()
