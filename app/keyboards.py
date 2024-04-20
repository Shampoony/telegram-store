from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.callback_answer import CallbackAnswer
from app.database.requests import get_categories, get_items_by_category
from app.admin import AdminProtect

menu_cd = CallbackAnswer("show_menu", "level", "category", "item_id")
buy_item = CallbackAnswer("buy", "item_id")


# С помощью этой функции будем формировать коллбек дату для каждого элемента меню, в зависимости от
# переданных параметров. Если Подкатегория, или айди товара не выбраны - они по умолчанию равны нулю
def make_callback_data(level, category="0", item_id="0"):
    return menu_cd.new(level=level, category=category, item_id=item_id)


admin_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Добавить товар'), KeyboardButton(text='Создать рассылку')],
                                            [KeyboardButton(text='Закрыть админ-меню ❌')]],resize_keyboard=True)
item_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Назад ◀'), KeyboardButton(text='Отмена ❌')]], resize_keyboard=True)

to_main = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='На главную', callback_data='to_main')]
        ])
to_back = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='На главную', callback_data='to_main_back')]
])
async def main_menu():
    CURRENT_LEVEL = 0
    inline_keyboard=[
                [InlineKeyboardButton(text='Каталог 🛍️', callback_data='catalog')],
                [InlineKeyboardButton(text='Отзывы 💬', callback_data='reviews', url='https://t.me/St0re_Reviews'),
                InlineKeyboardButton(text='Контакты 📋', callback_data='contacts'),
                InlineKeyboardButton(text='Канал 🌐', callback_data='channel')],
                
                [InlineKeyboardButton(text='Профиль 👤', callback_data='prof'),
                InlineKeyboardButton(text='Корзина 🗑', callback_data='mybasket')],
                ]
    main = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return main


async def basket(order_id, status):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Оформить заказ ✅', callback_data=f'order_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='◀ На главную', callback_data='to_main'))
    if status:
        keyboard.add(InlineKeyboardButton(text='Изменить товар 📝', callback_data=f'change_{order_id}'))
        keyboard.add(InlineKeyboardButton(text='Удалить товар ❌', callback_data=f'delete_{order_id}'))
    return keyboard.adjust(2).as_markup()

async def onlymybasket(order_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Купить ✅', callback_data=f'order_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='Отменить заказ 🔴', callback_data=f'delete_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='◀ На главную', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()

async def categories():
    CURRENT_LEVEL = 1
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    counter = 0
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                        callback_data=f'category_{category.id}'))
        counter += 1
    keyboard.add(InlineKeyboardButton(text='На главную', callback_data='to_main_back'))
    if counter == 0:
        return False
    return keyboard.adjust(2).as_markup()

async def items(category_id: int):
    items = await get_items_by_category(int(category_id))
    keyboard = InlineKeyboardBuilder()
    for item in items:
        keyboard.add(InlineKeyboardButton(text=item.name, callback_data=f'item_{item.id}'))
    return keyboard.adjust(2).as_markup()