
from .handlers import register_all_handlers
from .payment import register_payment_handlers
from .commands import register_commands_handler


def register_handlers(dp):
    register_commands_handler(dp)
    register_payment_handlers(dp)
    register_all_handlers(dp)
