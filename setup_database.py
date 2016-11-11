from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
    # from flask.ext.login import UserMixin
from datetime import datetime
import os

Base = declarative_base()

class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    username = Column(String(80),nullable=False, unique=True)
    password_hash = Column(String(80))
    picture = Column(String(80))
    email = Column(String(100), nullable=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash, password)

class Catalog(Base):

    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    timestamp = Column(DateTime, default=datetime.utcnow())
    items = relationship("Item", cascade="all, delete-orphan")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }

class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(150))
    price = Column(String(8))
    catalog_id = Column(Integer, ForeignKey('catalog.id'))
    catalog = relationship(Catalog, backref=backref("item", cascade="all, delete-orphan"))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    timestamp = Column(DateTime, default=datetime.utcnow())

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
        }

database_url = os.environ.get('DATABASE_URL') or 'sqlite:///itemcatalog.db'
engine = create_engine(database_url)

Base.metadata.create_all(engine)
