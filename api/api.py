import json
import inspect
from aiohttp import web
from collections import OrderedDict
from aiohttp.http_exceptions import  HttpBadRequest
from aiohttp.web_exceptions import HTTPMethodNotAllowed
from .models import AddressBook as abook
from .models import session


DEFAULT_METHODS = ('GET', 'POST', 'PUT', 'DELETE')


class RestEndpoint:

    def __init__(self):
        self.methods = {}

        for method_name in DEFAULT_METHODS:
            method = getattr(self, method_name.lower(), None)
            if method:
                self.register_method(method_name, method)

    def register_method(self, method_name, method):
        self.methods[method_name.upper()] = method

    async def dispatch(self, request: web.Request):
        method = self.methods.get(request.method.upper())
        if not method:
            raise HTTPMethodNotAllowed('', DEFAULT_METHODS)

        wanted_args = list(inspect.signature(method).parameters.keys())
        available_args = request.match_info.copy()
        available_args.update({'request': request})

        unsatisfied_args = set(wanted_args) - set(available_args.keys())
        if unsatisfied_args:
            raise HttpBadRequest('')

        try:
            return await method(**{arg_name: available_args[arg_name] for arg_name in wanted_args})
        except Exception as ex:
            template = "Server error, an exception of type {0} occurred. Arguments:{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            return web.Response(status=500, body=json.dumps({message: 500}), content_type='application/json')


class CollectionEndpoint(RestEndpoint):
    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    async def get(self) -> web.Response:
        data = []

        address_all = session.query(abook).all()
        for instance in self.resource.collection.values():
            data.append(self.resource.render(instance))
        data = self.resource.encode(data)
        return web.Response ( status=200, body=self.resource.encode({
            'address_all': [
                {'id': address.id, 'name': address.name, 'address': address.address,
                'number': address.number, 'email': address.email}

                    for address in session.query(abook)

                    ]
            }), content_type='application/json')

    async def post(self, request):
        data = await request.json()
        address = abook(name=data['name'],
                        address=data['address'],
                        number=data['number'],
                        email=data['email'])
        session.add(address)
        session.commit()
        return web.Response(status=201, body=self.resource.encode({
            'address': [
                {'id': address.id,
                'name': address.name,
                'address': address.address,
                'number': address.number,
                'email': address.email }

                    for address in session.query(abook)

                    ]
            }), content_type='application/json')


class InstanceEndpoint(RestEndpoint):
    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    async def get(self, instance_id):
        instance = session.query(abook).filter(abook.id == instance_id).first()
        if not instance:
            return web.Response(status=404, body=json.dumps({'not found': 404}), content_type='application/json')
        data = self.resource.render_and_encode(instance)
        return web.Response(status=200, body=data, content_type='application/json')

    async def put(self, request, instance_id):
        data = await request.json()

        address = session.query(abook).filter(abook.id == instance_id).first()
        if not address:
            return web.Response(status=404, body=json.dumps({'not found': 404}), content_type='application/json')
        address.name = data['name']
        address.address = data['address']
        address.number = data['number']
        address.email = data['email']
        session.add(address)
        session.commit()
        return web.Response(status=201, body=self.resource.render_and_encode(address),
                        content_type='application/json')

    async def delete(self, instance_id):
        address = session.query(abook).filter(abook.id == instance_id).first()
        if not address:
            return web.Response(status=404, body=json.dumps({'not found': 404}), content_type='application/json')
        session.delete(address)
        session.commit()
        return web.Response(status=20, body=json.dumps({'success': 200}), content_type='application/json')


class RestResource:
    def __init__(self, address, factory, collection, properties, id_field):
        self.address = address
        self.factory = factory
        self.collection = collection
        self.properties = properties
        self.id_field = id_field

        self.collection_endpoint = CollectionEndpoint(self)
        self.instance_endpoint = InstanceEndpoint(self)

    def register(self, router: web.UrlDispatcher):
        router.add_route('*', '/{address}/'.format(address=self.address), self.collection_endpoint.dispatch)
        router.add_route('*', '/{address}/{{instance_id}}'.format(address=self.address), self.instance_endpoint.dispatch)

    def render(self, instance):
        return OrderedDict((address, getattr(instance, address)) for address in self.properties)

    @staticmethod
    def encode(data):
        return json.dumps(data, indent=4).encode('utf-8')

    def render_and_encode(self, instance):
        return self.encode(self.render(instance))
