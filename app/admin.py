from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import app.keyboards as kb
from app.database.requests import get_users, set_item, set_category, get_item_by_id

admin = Router()

class Newsletter(StatesGroup):
    message = State()

admin_commands = 'Возможные команды:\n/newsletter - массовая рассылка всем пользователям бота\n/add_item - добалвени товара'


class AddItem(StatesGroup):
    name = State()
    category = State()
    description = State()
    photo = State()
    price = State()

    item_for_change = None

    texts = {
        'AddItem:name': 'Введите название заново',
        'AddItem:category': 'Введите категорию заново',
        'AddItem:description': 'Введите описание заново',
        'AddItem:photo': 'Введите фото заново',
        'AddItem:price': 'Введите цену заново'

    }
class AddCategory(StatesGroup):
    name = State()

class AdminProtect(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in [1190185138]


@admin.message(AdminProtect(),Command('apanel'))
async def apanel(message: Message):
    await message.answer(admin_commands, reply_markup=kb.admin_kb)

@admin.message(AdminProtect(),Command('newsletter'))
@admin.message(AdminProtect(), F.text == 'Создать рассылку')
async def newsletter(message: Message, state: FSMContext):
    await state.set_state(Newsletter.message)
    await message.answer('Отправте сообщение, которое вы хотите \
                        разослать всем пользователям бота')

@admin.message(AdminProtect(),Newsletter.message)
async def newsletter_message(message: Message, state: FSMContext):
    await message.answer('Подождите.. идёт рассылка.')
    for user in await get_users():
        try:
            await message.send_copy(chat_id=user.tg_id)
        except:
            pass
    await message.answer('Рассылка успешно завершена.')
    await state.clear()

@admin.message(AdminProtect(),F.text=='Закрыть админ-меню ❌')
async def close_menu(message: Message):
    await message.answer(f'<b>Админ-меню закрыто!</b>\n\nНапиши команду /start для выхода в главное меню', \
                        reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')

@admin.message(AdminProtect(), F.data.startswith('change_'))
async def change_item(callback: CallbackQuery):
    item_id = callback.data.split('_')[1]

    item_for_change = await get_item_by_id(item_id)

    AddItem.item_for_change = item_for_change
    await callback.answer()
    

@admin.message(AdminProtect(), F.text == 'Добавить товар')
@admin.message(AdminProtect(), Command('add_item'))
async def add_item(message: Message, state: FSMContext):
    await state.set_state(AddItem.name)
    await message.answer('Введите название товара', reply_markup=kb.item_kb)

@admin.message(AdminProtect(),Command('cancel'), StateFilter('*'))
@admin.message(AdminProtect(),F.text=='Отмена ❌', StateFilter('*'))
async def cancel_handler(message: Message, state: FSMContext):
    current_state= state.get_state()
    if current_state is None:
        return
    state.clear()
    await message.answer(text=f'Действия отменены', reply_markup=kb.admin_kb)

@admin.message(StateFilter('*'), Command("назад"), AdminProtect())
@admin.message(StateFilter('*'), F.text == "Назад ◀", AdminProtect())
async def back_step_handler(message: Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == AddItem.name:
        await message.answer('Предыдущего шага нет, или введите название товара или напишите "отмена"')
        return

    previous = None
    for step in AddItem.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"<b>Вы вернулись к прошлому шагу</b>\n\n{AddItem.texts[previous.state]}:", parse_mode='HTML')
            return
        previous = step




@admin.message(AdminProtect(), AddItem.name)
async def add_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddItem.category)
    if not await kb.categories():
        await message.answer('Нет доступных категорий\n\nОтправьте команду /cancel для отмены добавления товара, затем команду /add_category для добавление категории')
        return
    await message.answer(f'Выберете категорию', reply_markup=await kb.categories())



@admin.callback_query(AdminProtect(), AddItem.category)
async def add_item_category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=int(callback.data.split('_')[1]))
    await state.set_state(AddItem.description)
    await callback.answer('')
    await callback.message.answer('Введите описание товара')


@admin.message(AdminProtect(), AddItem.description)
async def add_item_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddItem.photo)
    await message.answer('Отправьте фото товара')


@admin.message(AdminProtect(), AddItem.photo, F.photo)
async def add_item_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AddItem.price)
    await message.answer('Введите цену товара')

@admin.message(AdminProtect(),Command('photo_url'), F.photo)
async def add_photo(message: Message):
    photo= message.photo[-1].file_id
    await message.answer(text=photo)
    

@admin.message(AdminProtect(), AddItem.price)
async def add_item_price(message: Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    data = await state.get_data()
    await set_item(data)
    await message.answer('Товар успешно добавлен')
    await state.clear()

@admin.message(AdminProtect(), F.text == 'Добавить Категорию')
@admin.message(AdminProtect(), Command('add_category'))
async def add_category(message: Message, state: FSMContext):
    await state.set_state(AddCategory.name)
    await message.answer('Введите категорию товара', reply_markup=kb.item_kb)

@admin.message(AdminProtect(), AddCategory.name)
async def add_category_to_db(message: Message, state: FSMContext):
    await state.update_data(name=str(message.text))
    data = await state.get_data()
    await set_category(data['name'])
    await message.answer('Категория успешно добавлена')
    await state.clear()


