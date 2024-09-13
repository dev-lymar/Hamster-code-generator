from aiogram import Dispatcher
from .handlers import handlers_router
from .payment import payment_router


def setup_routers(dp: Dispatcher):
    dp.include_router(payment_router)  # register handlers from payment.py
    dp.include_router(handlers_router)   # register handlers from handlers.py
