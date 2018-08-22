import os
import asyncio
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base


basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=sa.create_engine(SQLALCHEMY_DATABASE_URI))
session = scoped_session(Session)
Base = declarative_base()


class AddressBook(Base):

    __tablename__ = 'addressbook'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(50))
    address = sa.Column(sa.String(100))
    number = sa.Column(sa.Integer, unique=True)
    email = sa.Column(sa.String(50), unique=True)
