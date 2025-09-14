from sqlalchemy import BigInteger, ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from typing import List
from config import ENGINE, ECHO, DB_URL

engine = create_async_engine(url=ENGINE, echo=ECHO)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] =mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    basket_rel: Mapped['Basket'] = relationship(back_populates='user_rel')
class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    item_rel: Mapped['Item'] = relationship(back_populates='category_rel')
class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    photo: Mapped[str] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Numeric(5), nullable=False)
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    
    category_rel: Mapped['Category'] = relationship(back_populates='item_rel')
    basket_rel: Mapped['Basket'] = relationship(back_populates='item_rel')

class Basket(Base):
    __tablename__ = 'basket'
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[int] = mapped_column(ForeignKey('users.id'))
    item: Mapped[int] = mapped_column(ForeignKey('items.id'))

    user_rel: Mapped['User'] = relationship(back_populates='basket_rel')
    item_rel: Mapped['Item'] = relationship(back_populates='basket_rel')

class Banner(Base):
    __tablename__ = 'banner'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)