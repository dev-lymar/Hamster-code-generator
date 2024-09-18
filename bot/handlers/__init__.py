from .admin_handlers import register_admin_handlers
from .commands import register_commands_handler
from .handlers import register_all_handlers
from .message_handler import register_message_handler
from .payment_handlers import register_payment_handlers


def register_handlers(dp):
    register_commands_handler(dp)
    register_payment_handlers(dp)
    register_admin_handlers(dp)
    register_all_handlers(dp)
    register_message_handler(dp)
