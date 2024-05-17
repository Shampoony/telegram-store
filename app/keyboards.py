from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_categories, get_items_by_category, get_banner, get_category_by_id
from app.admin import AdminProtect

from aiogram.filters.callback_data import CallbackData


# С помощью этой функции будем формировать коллбек дату для каждого элемента меню, в зависимости от
# переданных параметров. Если Подкатегория, или айди товара не выбраны - они по умолчанию равны нулю



admin_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Добавить товар'), KeyboardButton(text='Создать рассылку')],
                                            [KeyboardButton(text='Закрыть админ-меню ❌')]],resize_keyboard=True)
item_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад ◀'), KeyboardButton(text='Отмена ❌')]], resize_keyboard=True)

to_main = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='На главную', callback_data='to_main')]
        ])
to_back = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='⬅ Назад', callback_data='main')]
])

async def main_menu():
    CURRENT_LEVEL = 0
    inline_keyboard=[
                [InlineKeyboardButton(text='Каталог 🛍️', callback_data='catalog_1')],
                [InlineKeyboardButton(text='Отзывы 💬', callback_data='reviews', url='https://t.me/St0re_Reviews'),
                InlineKeyboardButton(text='Контакты 📋', callback_data='contacts'),
                InlineKeyboardButton(text='Канал 🌐', callback_data='channel')],
                
                [InlineKeyboardButton(text='Профиль 👤', callback_data='prof'),
                InlineKeyboardButton(text='Корзина 🗑', callback_data='mybasket')],
                ]
    main = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return main


async def basket(order_id, status, category_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Оформить заказ ✅', callback_data=f'order_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='⬅ Назад', callback_data=f'category_{category_id}'))
    if status:
        keyboard.add(InlineKeyboardButton(text='Изменить товар 📝', callback_data=f'change_{order_id}'))
        keyboard.add(InlineKeyboardButton(text='Удалить товар ❌', callback_data=f'itemdelete_{order_id}'))
    return keyboard.adjust(2).as_markup()

async def onlymybasket(order_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Купить ✅', callback_data=f'buy_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='Отменить заказ 🔴', callback_data=f'delete_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='◀ Назад', callback_data='mybasket'))
    return keyboard.adjust(2).as_markup()

async def categories(status=True):
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    counter = 0
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                        callback_data=f'category_{category.id}'))
        counter += 1
    if status:
        keyboard.add(InlineKeyboardButton(text='⬅ Назад', callback_data=f'main_'))
    if counter == 0:
        return False
    return keyboard.adjust(2).as_markup()



async def items(category_id: int, status=False):
    items = await get_items_by_category(int(category_id))
    keyboard = InlineKeyboardBuilder()
    counter = 0
    for item in items:
        keyboard.add(InlineKeyboardButton(text=item.name, callback_data=f'item_{item.id}'))
        counter += 1
    if counter == 0:
        return False
    if status:
        keyboard.add(InlineKeyboardButton(text='📝 Изменить категорию', callback_data=f'categorychange_{category_id}'))
    keyboard.add(InlineKeyboardButton(text='⬅ Назад', callback_data=f'catalog'))
    return keyboard.adjust(2).as_markup()