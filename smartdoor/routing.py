# mysite/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack
import door.routing
from door.task_consumer import TaskConsumer

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            door.routing.websocket_urlpatterns
        )
    ),
    'door-control': ChannelNameRouter({
        "thumbnails-generate": TaskConsumer.connect,
        "thunbnails-delete": TaskConsumer.disconnect,
    })
})
