from app.database.models import User, Category, Item, Basket, Banner
from app.database.models import async_session

from sqlalchemy import select, update, delete

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()
            
async def set_item(data):
    async with async_session() as session:
        session.add(Item(**data))
        await session.commit()
async def set_basket(tg_id: int, item_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        session.add(Basket(user=user.id, item=item_id))
        await session.commit()
    
async def set_category(category_name : str):
    async with async_session() as session:
        session.add(Category(name=category_name))
        await session.commit()
async def set_image(data):
    async with async_session() as session:
        session.add(Banner(name=data['name'],image=data['image'], description=data['description']))
        await session.commit()

async def get_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users

async def get_user_by_id(tg_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user

async def get_basket(tg_id):
    async with async_session() as session:
        user = await get_user_by_id(tg_id)
        basket = await session.scalars(select(Basket).where(Basket.user==user.id))
        return basket

async def get_categories():
    async with async_session() as session:
        categories = await session.scalars(select(Category))
        return categories

async def get_all_photos():
    async with async_session() as session:
        photos = await session.scalars(select(Banner))
        return photos

async def get_items_by_category(category_id: int):
    async with async_session() as session:
        items = await session.scalars(select(Item).where(Item.category == category_id))
        return items

async def get_category_by_id(category_id: int):
    async with async_session() as session:
        return await session.scalar(select(Category).where(Category.id==category_id))

async def get_item_by_id(item_id: int):
    async with async_session() as session:
        item = await session.scalar(select(Item).where(Item.id == int(item_id)))
        return item

async def get_banner(banner_name:str):
    async with async_session() as session:
        banner = await session.scalar(select(Banner).where(Banner.name==banner_name))
        return banner
    
async def get_image_by_name(name: str):
    async with async_session() as session:
        image = await session.scalar(select(Banner).where(Banner.name==name))
        return image


async def delete_basket(tg_id: int, item_id: int):
    async with async_session() as session:
        user = await get_user_by_id(tg_id)
        await session.execute(delete(Basket).where(Basket.user == user.id, Basket.item == item_id))
        await session.commit()

async def delete_item(item_id: int):
    async with async_session() as session:
        await session.execute(delete(Item).where(Item.id==item_id))
        await session.commit()
async def delete_category_by_id(category_id: int):
    async with async_session() as session:
        await session.execute(delete(Category).where(Category.id==category_id))
        await session.commit()

async def delete_photo_by_name(name: str):
    async with async_session() as session:
        await session.execute(delete(Banner).where(Banner.name==name))
        await session.commit()


async def update_item(item_id: int, data):
    async with async_session() as session:
        query = update(Item).where(Item.id==item_id).values(
            name=data['name'],
            category=data['category'],
            description=data['description'],
            photo=data['photo'],
            price=data['price']
        )
        await session.execute(query)
        await session.commit()

async def update_category(category_id: int, category_name): 
    async with async_session() as session:
        query = update(Category).where(Category.id==category_id).values(
            name=category_name
        )
        await session.execute(query)
        await session.commit()
