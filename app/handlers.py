from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command

import app.keyboards as kb
from app.database.requests import get_item_by_id, set_user, set_basket, get_user_by_id, get_basket, delete_basket
from app.admin import AdminProtect


router = Router()

@router.message(CommandStart())
@router.callback_query(F.data.startswith('to_main'))
async def cmd_start(message: Message):
    if isinstance(message, Message):
        await set_user(message.from_user.id)
        await message.answer("Добро пожаловать в интернет-магазин!",
                            reply_markup=await kb.main_menu())
    else:
        if len(message.data.split('_')) > 2:
            await message.message.edit_text(text="Добро пожаловать в интернет-магазин!",
                                reply_markup=await kb.main_menu())
        else:
            await message.message.answer("Добро пожаловать в интернет магазин!",
                                        reply_markup=await kb.main_menu())


@router.callback_query(F.data=='catalog')
async def catalog(callback: CallbackQuery):
    markup = await kb.categories()
    await callback.answer('')
    await callback.message.edit_text(text='Выберете категорию.', reply_markup=markup)
    
@router.callback_query(F.data=='contacts')
async def catalog(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text(text='<b>Контакты</b>\n\nДля наших любимых покупателей предусмотрен данный сервис, где вы можете спокойно\
                                    обратиться к нам с вашими предложениями\nАдмин - @Cheebupelka\nПросто крутой челик - @OdoFlamingo135',\
                                    parse_mode='HTML', reply_markup=kb.to_back)
    
@router.callback_query(F.data=='prof')
async def profile(callback: CallbackQuery):
    items = await get_basket(callback.from_user.id)
    kol = 0
    for item in items:
        kol += 1
    message_text = f'<b>👤 Username: {callback.from_user.first_name}</b>\n\n'
    if AdminProtect():
        message_text += '🟢 <b>Статус</b>: Админ'
    else:
        message_text += '🟢 <b>Статус</b> Клиент'
    message_text += f'\n\n\n<b>🔐 Телеграм ID: {callback.from_user.id}\n\n</b><b>💌  Электронная почта:</b> Не привязана\n\n\
<b>🛒 Количество товаров в корзине:</b> {kol}\n\n'
    await callback.answer('')
    await callback.message.edit_text(text=message_text,\
                                    parse_mode='HTML', reply_markup=kb.to_back)

@router.callback_query(F.data.startswith('category_'))
async def category (callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Выберете товар', 
                                    reply_markup=await kb.items(callback.data.split('_')[1]))


@router.callback_query(F.data.startswith('item_'))
async def category (callback: CallbackQuery):
    item = await get_item_by_id(int(callback.data.split('_')[1]))
    await callback.answer('')
    await callback.message.answer_photo(photo = item.photo, caption=f'{item.name}\n\n{item.description}\n\nЦена: {item.price} рублей'\
                                        ,reply_markup=await kb.basket(item.id, AdminProtect()))

@router.callback_query(F.data.startswith('basket_item_'))
async def onlymybasket(callback: CallbackQuery):
    item = await get_item_by_id(callback.data.split('_')[2])
    await callback.message.answer_photo(photo = item.photo, caption=f'{item.name}\n\n{item.description}\n\nЦена: {item.price} рублей'\
                                        ,reply_markup=await kb.onlymybasket(order_id=item.id))

@router.callback_query(F.data.startswith('order_'))
async def basket(callback: CallbackQuery):
    await set_basket(callback.from_user.id, callback.data.split('_')[1])
    await callback.answer('Товар добален в корзину')

@router.callback_query(F.data == 'mybasket')
async def mybasket(callback: CallbackQuery):
    await callback.answer('')
    items = await get_basket(callback.from_user.id)
    keyboard = []
    for item in items:
        prod = await get_item_by_id(item.item)
        keyboard.append([InlineKeyboardButton(text=f'Название: {prod.name} Цена: {prod.price}₽', callback_data=f'basket_item_{item.item}')])
    if len(keyboard) == 0:
        await callback.message.answer('Ваша корзина пуста.')
    else:
        await callback.message.answer(text=f'Ваша корзина,\n ', reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith('delete_'))
async def delete_from_basket(callback: CallbackQuery):
    await delete_basket(callback.from_user.id, callback.data.split('_')[1])
    await callback.message.delete()
    await callback.answer('Вы удалили товар из корзины')