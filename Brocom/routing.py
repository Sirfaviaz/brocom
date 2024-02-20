from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from user import consumers  # Adjust the import based on your app structure

application = ProtocolTypeRouter({
    'websocket': URLRouter(
        [
            path('ws/order_confirmation/', consumers.OrderConfirmationConsumer.as_asgi()),
            path('ws/address/', consumers.AddressConsumer.as_asgi()),
            # Add more WebSocket paths as needed
        ]
    ),
})