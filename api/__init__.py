from aiohttp.web import Application
from .api import RestResource
from .models import AddressBook



address = {}
app = Application()
person_resource = RestResource('address', AddressBook, address, ('name', 'address', 'number', 'email'), 'id')
person_resource.register(app.router)
