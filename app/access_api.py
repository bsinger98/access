import itertools

from aiohttp import web
from aiohttp_jinja2 import template

from app.objects.secondclass.c_fact import Fact
from app.service.auth_svc import check_authorization


class AccessApi:

    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.rest_svc = services.get('rest_svc')
        self.auth_svc = services.get('auth_svc')

    @check_authorization
    @template('access.html')
    async def landing(self, request):
        search = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        return dict(agents=[a.display for a in await self.data_svc.locate('agents', match=search)])

    @check_authorization
    async def exploit(self, request):
        data = dict(await request.json())
        converted_facts = [Fact(trait=f['trait'], value=f['value']) for f in data.get('facts')]
        await self.rest_svc.task_agent_with_ability(data['paw'], data['ability_id'], converted_facts)
        return web.json_response('complete')

    @check_authorization
    async def abilities(self, request):
        search = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        data = dict(await request.json())
        agent = (await self.data_svc.locate('agents', dict(paw=data['paw'])))[0]
        abilities_by_executor = [await self.data_svc.locate('abilities', dict(executor=ex)) for ex in agent.executors]
        capable_abilities = await agent.capabilities(list(itertools.chain.from_iterable(abilities_by_executor)))
        return web.json_response([x.display for x in capable_abilities if x.access in search['access']])
