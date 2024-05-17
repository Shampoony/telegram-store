from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import app.keyboards as kb
from app.database.requests import get_item_by_id, set_user, set_basket, get_user_by_id, get_basket, delete_basket, get_banner, get_category_by_id,update_category
from app.admin import AdminProtect


router = Router()

@router.message(CommandStart())
@router.callback_query(F.data.startswith('main'))
async def cmd_start(message: Message):
    banner = await get_banner('main')
    media = InputMediaPhoto(media=banner.image, caption=banner.description)
    if isinstance(message, Message):
        await set_user(message.from_user.id)
        await message.answer_photo(photo=banner.image, caption=banner.description,
                            reply_markup=await kb.main_menu())
    else:
        if len(message.data.split('_')) > 1:
            await message.message.edit_media(media,
                                reply_markup=await kb.main_menu())
            
        else:
            await message.message.edit_media(media,
                                reply_markup=await kb.main_menu())


@router.callback_query(F.data.startswith('catalog'))
async def catalog(callback: CallbackQuery):
    banner = InputMediaPhoto(media=(await get_banner('catalog')).image, caption=(await get_banner('catalog')).description)
    markup = await kb.categories(1)
    await callback.answer('')
    await callback.message.edit_media(banner, reply_markup=markup)
    
@router.callback_query(F.data=='contacts')
async def catalog(callback: CallbackQuery):
    await callback.answer('')
    media = InputMediaPhoto(media=(await get_banner('contacts')).image, caption='<b>Контакты</b>\n\nДля наших любимых покупателей\
                                    предусмотрен данный сервис, где вы можете спокойно\
                                    обратиться к нам с вашими предложениями\nАдмин - @Cheebupelka\nПросто крутой челик - @OdoFlamingo135',\
                                    parse_mode='HTML')
    await callback.message.edit_media(media, reply_markup=kb.to_back)
    
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
    media = InputMediaPhoto(media=(await get_banner('prof')).image, caption=message_text, parse_mode='HTML')
    await callback.answer('')
    await callback.message.edit_media(media, reply_markup=kb.to_back)

@router.callback_query(F.data.startswith('category_'))
async def category (callback: CallbackQuery):
    await callback.answer()
    category = await get_category_by_id(int(callback.data.split('_')[1]))
    banner = await get_banner(category.name.split(' ')[0])
    if not banner:
        banner = await get_banner('not_found')
        banner.description = ''
    media = InputMediaPhoto(media=banner.image, caption=banner.description)
    if not (await kb.items(int(callback.data.split('_')[1]))):
        media = InputMediaPhoto(media=banner.image, caption='К сожалению, в этой категории пока нет товаров...')
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text='⬅ Назад', callback_data=f'catalog'))
        await callback.message.edit_media(media, reply_markup=keyboard.adjust(2).as_markup())
        return
    await callback.message.edit_media(media, 
                                    reply_markup=await kb.items(int(callback.data.split('_')[1]), AdminProtect()))


@router.callback_query(F.data.startswith('item_'))
async def category (callback: CallbackQuery):
    item = await get_item_by_id(int(callback.data.split('_')[1]))
    media = InputMediaPhoto(media=item.photo, caption=f'<b>{item.name}</b>\n\n{item.description}\n\n<b>Cтоимость: {round(item.price)}₽</b>', parse_mode='HTML')
    await callback.answer('')
    await callback.message.edit_media(media\
                                        ,reply_markup=await kb.basket(item.id, AdminProtect(), item.category))

@router.callback_query(F.data.startswith('basket_item_'))
async def onlymybasket(callback: CallbackQuery):
    item = await get_item_by_id(callback.data.split('_')[2])
    media = InputMediaPhoto(media=item.photo, caption=f'<b>{item.name}</b>\n\n<b>{item.description}</b>\n\n<b>Cтоимость: {round(item.price)}₽</b>', parse_mode='HTML')
    await callback.message.edit_media(media\
                                        ,reply_markup=await kb.onlymybasket(order_id=item.id))

@router.callback_query(F.data.startswith('buy_'))
async def buy_item(callback: CallbackQuery):
    item = await get_item_by_id(callback.data.split('_')[-1])
    await callback.message.answer(text='Большое спасибо тебе за покупку! Свяжись с продавцом напрямую.\
                                Данный продавец проверен многими пользователями,\
                                в чём ты можешь убедиться по отзывам в нащем канале.')

@router.callback_query(F.data.startswith('order_'))
async def basket(callback: CallbackQuery):
    await set_basket(callback.from_user.id, int(callback.data.split('_')[1]))
    await callback.answer('Товар добален в корзину')

@router.callback_query(F.data == 'mybasket')
async def mybasket(callback: CallbackQuery):
    await callback.answer('')
    items = await get_basket(callback.from_user.id)
    keyboard = []
    for item in items:
        prod = await get_item_by_id(item.item)
        keyboard.append([InlineKeyboardButton(text=f'Название: {prod.name} Цена: {round(prod.price)}₽', callback_data=f'basket_item_{item.item}')])
    keyboard.append([InlineKeyboardButton(text=f'⬅ Назад', callback_data=f'main')])
    banner = await get_banner('cart')
    media = InputMediaPhoto(media=banner.image, caption=banner.description)
    if len(keyboard) == 0:
        media = InputMediaPhoto(media=banner.image, caption='Ваша корзина пуста.')
        await callback.message.edit_media(media)
    else:
        await callback.message.edit_media(media, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@router.callback_query(F.data.startswith('delete_'))
async def delete_from_basket(callback: CallbackQuery):
    await delete_basket(callback.from_user.id, int(callback.data.split('_')[1]))
    await callback.message.delete()
    await callback.answer('Вы удалили товар из корзины')
@router.callback_query(F.data == 'channel')
async def channel(callback: CallbackQuery):
    await callback.answer('Канал всё еще в разработке.')

#@router.callback_query(F.data.startswith('back_'))
#async def back(callback: CallbackQuery):
#    level = int(callback.data.split('_')[1], 'main')
#    await get_menu_content(level-1)