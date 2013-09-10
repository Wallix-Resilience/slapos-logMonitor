from pymongo import Connection
from pymongo.errors import AutoReconnect


Connection(nodes[-1], slave_okay=True, ssl=SSL).admin.command("replSetInitiate", config)
