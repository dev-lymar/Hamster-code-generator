import asyncio

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import BOT_ID
from handlers.handlers import send_keys_menu, show_info_message
from keyboards.back_to_main_kb import get_back_to_main_menu_button

from keyboards.donate_kb import get_payment_keyboard, get_cancel_donation_keyboard

from states.form import DonationState
from utils.helpers import get_translation

payment_router = Router()


@payment_router.callback_query(F.data == "donate_custom")
async def donate_custom_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id
    message_text = await get_translation(user_id, "donate_custom_prompt")
    keyboard = await get_cancel_donation_keyboard(user_id)

    # Send a message asking for the amount and memorise its ID
    message = await callback.message.answer(
        text=message_text,
        reply_markup=keyboard
    )

    # Save the message ID for deletion
    await state.update_data(message_to_delete=message.message_id)
    await state.set_state(DonationState.waiting_for_amount)
    await callback.answer()


@payment_router.callback_query(F.data == "cancel_custom_donation", DonationState.waiting_for_amount)
async def cancel_custom_donation_handler(callback: types.CallbackQuery, state: FSMContext):
    await show_info_message(callback)

    await state.clear()


@payment_router.message(DonationState.waiting_for_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    invalid_amount_text = await get_translation(user_id, "invalid_amount_message")
    invalid_input_text = await get_translation(user_id, "invalid_input_message")
    refund_error_text = await get_translation(user_id, "refund_error_message")
    keyboard = await get_cancel_donation_keyboard(user_id)

    try:
        amount = int(message.text)
        if not (1 <= amount <= 2500):
            await message.delete()
            await message.answer(
                text=invalid_amount_text,
                reply_markup=keyboard
            )
            return

    except ValueError:
        await message.delete()
        await message.answer(
            text=invalid_input_text,
            reply_markup=keyboard
        )
        return

    await message.delete()
    data = await state.get_data()
    message_to_delete = data.get('message_to_delete')
    if message_to_delete:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=message_to_delete)
        except TelegramBadRequest:
            pass

    try:
        await send_invoice_message(message, amount, state)
    except TelegramBadRequest as error_message:
        await message.answer(refund_error_text.format(error_message=error_message))


@payment_router.callback_query(F.data.startswith("donate_"))
async def donate_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    await send_invoice_message(callback.message, amount, state)
    await callback.answer()


@payment_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@payment_router.message(F.content_type == types.ContentType.SUCCESSFUL_PAYMENT)
async def success_payment_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    invoice_success_text = await get_translation(user_id, "invoice_success_message")

    # Get the invoice message ID from the state
    data = await state.get_data()
    invoice_message_id = data.get('invoice_message_id')
    if invoice_message_id:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=invoice_message_id)

    await message.answer(text=invoice_success_text)
    await state.clear()
    await send_keys_menu(message, state)


@payment_router.callback_query(F.data == "cancel_payment")
async def cancel_payment_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id if callback.from_user.id != BOT_ID else callback.chat.id
    payment_cancelled_text = await get_translation(user_id, "payment_cancelled_message")

    # Delete the invoice message
    await callback.message.delete()
    await callback.answer(payment_cancelled_text)


@payment_router.message(F.text.startswith("/refund_stars"))
async def refund_stars_command_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    refund_prompt_text = await get_translation(user_id, "refund_prompt_message")
    refund_success_text = await get_translation(user_id, "refund_success_message")
    refund_transaction_not_found_text = await get_translation(user_id, "refund_transaction_not_found_message")
    refund_already_processed_text = await get_translation(user_id, "refund_already_processed_message")
    refund_error_text = await get_translation(user_id, "refund_error_message")

    # Get the transaction number from the command
    transaction_id = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    if not transaction_id:
        await message.answer(refund_prompt_text)
        return

    try:
        # Use the Telegram method for refunds
        await message.bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        )
        await message.answer(refund_success_text)

        await send_keys_menu(message, state)

    except TelegramBadRequest as error:
        # Handling possible return errors
        if "CHARGE_NOT_FOUND" in error.message:
            await message.answer(refund_transaction_not_found_text)
        elif "CHARGE_ALREADY_REFUNDED" in error.message:
            await message.answer(refund_already_processed_text)
            await asyncio.sleep(2)
            await send_keys_menu(message, state)
        else:
            await message.answer(refund_error_text.format(error_message=error.message))

    await state.clear()


@payment_router.message(F.text == "/paysupport")
async def paysupport_handler(message: types.Message):
    user_id = message.from_user.id if message.from_user.id != BOT_ID else message.chat.id
    await message.delete()
    paysupport_prompt_text = await get_translation(user_id, "paysupport_prompt_message")
    keyboard = await get_back_to_main_menu_button(user_id)

    await message.answer(text=paysupport_prompt_text, reply_markup=keyboard)


async def send_invoice_message(callback_or_message, amount: int, state: FSMContext):
    user_id = callback_or_message.from_user.id if callback_or_message.from_user.id != BOT_ID \
        else callback_or_message.chat.id
    keyboard = await get_payment_keyboard(user_id)
    invoice_title_text = await get_translation(user_id, "invoice_title_message")
    invoice_description_text = await get_translation(user_id, "invoice_description_message")

    prices = [types.LabeledPrice(label="XTR", amount=amount)]
    invoice_message = await callback_or_message.answer_invoice(
        title=invoice_title_text,
        description=invoice_description_text.format(amount=amount),
        prices=prices,
        provider_token="",
        payload="channel_support",
        currency="XTR",
        reply_markup=keyboard
    )
    # Save the invoice message ID to a state
    await state.update_data(invoice_message_id=invoice_message.message_id)