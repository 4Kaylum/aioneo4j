import asyncio
import collections
import typing

from yarl import URL

from .transport import Transport


class Client(object):
    r"""A Neo4j client object, used to interface with your Neo4j database

    Parameters
    -----------
    host: :class:`str`
        The host URL that we want to connect to via HTTP.
    port: :class:`int`
        The port that we want to connect to the database via.
    user: :class:`str`
        The username we want to authenticate as.
    password: :class:`str`
        The password we want to authenticate our user as.
    database: :class:`str`
        The database you want to connect to.
    transport: Optional[:class:`Transport`]
        The aiohttp transport method for actually performing given requests.
    request_timeout: Optional[:class:`float`]
        How long a request should wait to process before timing out.
    """

    def __init__(self, host:str="127.0.0.1", port:int=7474, user:str=None, password:str=None, database:str=None, transport:Transport=Transport, request_timeout:float=..., *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        url = URL(f"http://{host}:{port}")
        auth = (user, password,)
        self.transport = transport(
            url=url,
            auth=auth,
            database=database,
            request_timeout=request_timeout,
            loop=self.loop,
        )

    def get_auth(self):
        return self.transport.auth

    def set_auth(self, auth):
        self.transport.auth = auth

    auth = property(get_auth, set_auth)
    del get_auth, set_auth

    async def cypher(self, query:str, path:str='tx/commit', request_timeout:float=..., **params):
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

    # async def transaction_commit(self, *statements, path='db/data/transaction/commit', request_timeout=...):
    #     r"""Commit a transaction"""

    #     # Parse out the multiple statements given
    #     if len(statements) == 1 and isinstance(statements[0], collections.Mapping) and 'statements' in statements[0]:
    #         request = statements[0]
    #     else:
    #         request = {'statements': []}

    #         for statement in statements:
    #             if not isinstance(statement, collections.Mapping):
    #                 statement = {'statement': statement}
    #             else:
    #                 if 'statement' not in statement:
    #                     raise ValueError

    #             request['statements'].append(statement)

    #     _, data = await self.transport.perform_request(
    #         'POST',
    #         path,
    #         data=request,
    #         request_timeout=request_timeout,
    #     )
    #     return data

    # async def indexes(self, path='db/data/schema/index', request_timeout=...):
    #     _, data = await self.transport.perform_request(
    #         'GET',
    #         path,
    #         request_timeout=request_timeout,
    #     )
    #     return data

    # async def constraints(self, path='db/data/schema/constraint', request_timeout=...):
    #     _, data = await self.transport.perform_request(
    #         'GET',
    #         path,
    #         request_timeout=request_timeout,
    #     )
    #     return data

    # async def user_password(self, password, username='neo4j', path='user/{username}/password', set_auth=False, request_timeout=...):
    #     path = path.format(username=username,)
    #     request = {'password': password}
    #     _, data = await self.transport.perform_request(
    #         'POST',
    #         path,
    #         data=request,
    #         request_timeout=request_timeout,
    #     )
    #     if set_auth:
    #         auth = username, password
    #         self.auth = auth
    #     return data

    async def close(self):
        await self.transport.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()
