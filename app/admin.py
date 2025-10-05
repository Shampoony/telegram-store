import asyncio
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from aiogram.filters import CommandStart, Command, Filter, StateFilter, or_f
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto

import app.keyboards as kb
from app.database.requests import get_users, set_item, set_category, get_item_by_id, update_item, delete_item,\
    set_image,delete_category_by_id,get_category_by_id, update_category, delete_photo_by_name, get_all_photos

admin = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Newsletter(StatesGroup):
    message = State()

admin_commands = 'Возможные команды:\n/newsletter - массовая рассылка всем пользователям бота\n/add_item - добавление товара\n\
/add_category - добавление категории\n/del_category - Удаление категории\n/add_photo - добавление картинки для меню\n'


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
    category_for_change = None

class AddImage(StatesGroup):
    name = State()
    description = State()
    image = State()
class DeleteImage(StatesGroup):
    name=State()
class DeleteCategory(StatesGroup):
    id = State()

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

@admin.message(AdminProtect(), Newsletter.message)
async def newsletter_message(message: Message, state: FSMContext):
    await message.answer('🚀 Начинаю рассылку...')
    
    users = await get_users()
    users_list = list(users)  # Преобразуем ScalarResult в список
    total_users = len(users_list)
    success_count = 0
    blocked_count = 0
    error_count = 0
    
    # Отправляем батчами по 20 пользователей
    batch_size = 20
    
    for i in range(0, total_users, batch_size):
        batch = users_list[i:i + batch_size]
        
        # Создаем задачи для параллельной отправки
        tasks = []
        for user in batch:
            task = send_to_user(message, user.tg_id)
            tasks.append(task)
        
        # Ждем выполнения всех задач в батче
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Подсчитываем результаты
        for result in results:
            if result == "success":
                success_count += 1
            elif result == "blocked":
                blocked_count += 1
            else:
                error_count += 1
        
        # Небольшая пауза между батчами
        if i + batch_size < total_users:
            await asyncio.sleep(1)
        
        # Обновляем прогресс каждые 100 пользователей
        if (i + batch_size) % 100 == 0 or i + batch_size >= total_users:
            current = min(i + batch_size, total_users)
            await message.answer(
                f"📊 Прогресс: {current}/{total_users}\n"
                f"✅ Успешно: {success_count}\n"
                f"🚫 Заблокировали: {blocked_count}\n"
                f"❌ Ошибки: {error_count}"
            )
    
    # Финальный отчет
    await message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"📈 Статистика:\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Доставлено: {success_count}\n"
        f"🚫 Заблокировали бота: {blocked_count}\n"
        f"❌ Ошибки: {error_count}\n"
        f"📊 Успешность: {success_count/total_users*100:.1f}%"
    )
    
    await state.clear()


async def send_to_user(message: Message, user_id: int) -> str:
    """Отправка сообщения одному пользователю с обработкой ошибок"""
    try:
        await message.send_copy(chat_id=user_id)
        return "success"
        
    except TelegramForbiddenError:
        logger.info(f"User {user_id} blocked the bot")
        return "blocked"
        
    except TelegramRetryAfter as e:
        # Слишком много запросов, ждем и повторяем
        logger.warning(f"Rate limit hit, waiting {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        try:
            await message.send_copy(chat_id=user_id)
            return "success"
        except:
            return "error"
            
    except Exception as e:
        logger.error(f"Error sending to user {user_id}: {e}")
        return "error"
    

@admin.message(AdminProtect(),F.text=='Закрыть админ-меню ❌')
async def close_menu(message: Message):
    await message.answer(f'<b>Админ-меню закрыто!</b>\n\nНапиши команду /start для выхода в главное меню', \
                        reply_markup=ReplyKeyboardRemove(), parse_mode='HTML')

@admin.callback_query(AdminProtect(), F.data.startswith('itemdelete_'), StateFilter(None))
async def del_item(callback: CallbackQuery):
    item_id = callback.data.split('_')[1]
    await delete_item(int(item_id))
    await callback.answer('Товар успешно удалён!')
    await callback.message.delete()

@admin.callback_query(AdminProtect(), F.data.startswith('change_'), StateFilter(None))
async def change_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split('_')[1]

    item_for_change = await get_item_by_id(item_id)

    AddItem.item_for_change = item_for_change
    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddItem.name)

@admin.message(AdminProtect(), F.text == 'Добавить товар', StateFilter(None))
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


@admin.message(AdminProtect(), AddItem.name, or_f(F.text, F.text=='.'))
async def add_item_name(message: Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name=AddItem.item_for_change.name)
        await message.answer(text='Название осталось прежним')
    else:
        if len(message.text) > 50:
            await message.answer('Введите название, которое содержит меньше 50 символов!.\nВведи заново')
            return
        await state.update_data(name=message.text)

    await state.set_state(AddItem.category)
    if not await kb.categories():
        await message.answer('Нет доступных категорий\n\nОтправьте команду /cancel для отмены добавления товара, затем команду /add_category для добавление категории')
        return
    await message.answer(f'Выберете категорию', reply_markup=await kb.categories(False))



@admin.callback_query(AdminProtect(), AddItem.category, or_f(F.data, F.text=='.'))
async def add_item_category(callback: CallbackQuery, state: FSMContext):
    if callback.message.text == '.':
        await state.update_data(category=AddItem.item_for_change.category)
        await callback.message.answer(text='Категория осталась прежней')
    else:
        await state.update_data(category=int(callback.data.split('_')[1]))
    await state.set_state(AddItem.description)
    await callback.answer('')
    await callback.message.answer('Введите описание товара')


@admin.message(AdminProtect(), AddItem.description, or_f(F.text, F.text=='.'))
async def add_item_description(message: Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(description=AddItem.item_for_change.description)
        await message.answer(text='Описание осталось прежним')
    else:
        if len(message.text) > 200:
            await message.answer('Введите название, которое содержит меньше 200 символов!.\nВведи заново')
            return
        await state.update_data(description=message.text)

    await state.update_data(description=message.text)
    await state.set_state(AddItem.photo)
    await message.answer('Отправьте фото товара')


@admin.message(AdminProtect(), AddItem.photo, or_f(F.photo, F.text=='.'))
async def add_item_photo(message: Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(photo=AddItem.item_for_change.photo)
        await message.answer('Фото товара осталось прежним.')
    else:
        await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AddItem.price)
    await message.answer('Введите цену товара')


@admin.message(AdminProtect(), AddItem.price, or_f(F.text, F.text=='.'))
async def add_item_price(message: Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(price=AddItem.item_for_change.price)
        await message.answer('Цена товара осталась прежней.')
    else:
        await state.update_data(price=float(message.text))
    data = await state.get_data()
    try:
        if AddItem.item_for_change:
            await update_item(AddItem.item_for_change.id, data)
            addition = 'изменён'
        else:
            await set_item(data)
            addition = 'добавлен'
        await message.answer(f'Товар успешно {addition}', reply_markup=kb.admin_kb)
        await state.clear()
    except Exception as e:
        await message.answer(
            f'Ошибка: {str(e)}\nОбратись к программисту, он опять денег хочет', reply_markup=kb.admin_kb
        )
        await state.clear()
    AddItem.item_for_change = None

@admin.callback_query(AdminProtect(), F.data.startswith('categorychange_'))
async def cahnge_category(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split('_')[1]

    category_for_change = await get_category_by_id(int(category_id))

    AddCategory.category_for_change = category_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название категории",reply_markup=kb.item_kb
    )
    await state.set_state(AddCategory.name)

@admin.message(AdminProtect(), F.text == 'Добавить Категорию')
@admin.message(AdminProtect(), Command('add_category'))
async def add_category(message: Message, state: FSMContext):
    await state.set_state(AddCategory.name)
    await message.answer('Введите название категории', reply_markup=kb.item_kb)

@admin.message(AdminProtect(), AddCategory.name)
async def add_category_to_db(message: Message, state: FSMContext):
    await state.update_data(name=str(message.text))
    data = await state.get_data()
    if AddCategory.category_for_change:
        await update_category(AddCategory.category_for_change.id,data['name'])
        addition = 'изменена'
    else:
        addition = 'добавлена'
        await set_category(data['name'])
    await message.answer(f'Категория успешно {addition}', reply_markup=ReplyKeyboardRemove())
    await state.clear()

@admin.message(AdminProtect(), F.text == 'Удалить Категорию', StateFilter(None))
@admin.message(AdminProtect(), Command('del_category'))
async def delete_category(message: Message, state: FSMContext):
    await state.set_state(DeleteCategory.id)
    await message.answer('Выберете категорию товара', reply_markup=await kb.categories(False))

@admin.callback_query(AdminProtect(), DeleteCategory.id, F.data)
async def delete_catgory_finish(callback: CallbackQuery, state: FSMContext):
    await state.update_data(id=int(callback.data.split('_')[1]))
    data = await state.get_data()
    await delete_category_by_id(data['id'])
    await callback.message.answer('Категория успешно удалена!\nОтправьте команду /start для выхода в главное меню', reply_markup=ReplyKeyboardRemove())
    await state.clear()


@admin.message(AdminProtect(), Command('add_photo'))
async def add_photo_name(message: Message, state: FSMContext):
    await state.set_state(AddImage.name)
    await message.answer('Введите название изображение <strong>(исключительно на латинице)</strong>', parse_mode='HTML')

@admin.message(AdminProtect(), AddImage.name, F.text)
async def add_photo_description(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddImage.description)
    await message.answer('Введите описание для изображения(Оно будет отображаться под картинкой)')

@admin.message(AdminProtect(), AddImage.description, F.text)
async def add_photo_image(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddImage.image)
    await message.answer('Пришлите картику')

@admin.message(AdminProtect(),AddImage.image, F.photo)
async def add_photo_data(message: Message, state: FSMContext):
    img = message.photo[-1].file_id
    await state.update_data(image=img)
    data = await state.get_data()
    await set_image(data)
    await message.answer(f'Картинка успешно добавлена!\nОтправьте команду /start чтобы выйти\n')
    await state.clear()


@admin.message(AdminProtect(), Command('del_photo'))
async def del_photo(message: Message, state: FSMContext):
    await message.answer(text='Введите имя фото')
    await state.set_state(DeleteImage.name)

@admin.message(AdminProtect(), Command('get_photos'))
async def get_photos(message: Message, state: FSMContext):
    photos = await get_all_photos()
    media = []
    for photo in photos:
        media.append(InputMediaPhoto(media=photo.image, caption=photo.name))
    await message.answer_media_group(media=media)


@admin.message(AdminProtect(), DeleteImage.name)
async def delete_photo(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    await delete_photo_by_name(data['name'])
    await message.answer('Картинка успешно удалена!')
    await state.clear()

@admin.message(AdminProtect(),Command('photo_url'), F.photo)
async def add_photo(message: Message):
    photo= message.photo[-1].file_id
    await message.answer(text=photo)
