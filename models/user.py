﻿import re
import hashlib


from datetime       import datetime, date
from sqlalchemy.orm import validates
from sqlalchemy     import (Column, Boolean, Integer, String, DateTime, Date,ForeignKey, ARRAY )

from .base              import Base
from sqlalchemy_utils   import EmailType

# User Profile, also used for those not signed in
class Users( Base ):
    __tablename__ = 'users'

    id            = Column(Integer, primary_key=True)
    email         = Column(EmailType)
    password      = Column(String)
    title         = Column(String)
    first_name    = Column(String)
    last_name     = Column(String)
    provider_type = Column(String)
    practice_name = Column(String)
    practice_type = Column(String)
    expires       = Column(Date)
    joined        = Column(Date, default=date.today)

    # Login booleans
    active        = Column( Boolean, default = False )
    authenticated = Column( Boolean, default = False )

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def set_password(self, raw_password):
        h = hashlib.md5()
        h.update(raw_password.encode('utf-8'))
        self.password = h.hexdigest()

    def check_password(self, raw_password):
        h = hashlib.md5()
        h.update(raw_password)
        if self.password == h.hexdigest():
            return True

        return False

    def get_id(self):
        return self.id

    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"


class Requests(Base):
    __tablename__ = 'requests'
    id      = Column(Integer, primary_key=True)
    user    = Column(ForeignKey('users.id'))
    ip      = Column(String)
    zipcode = Column(String)
    plan    = Column(String)
    drug    = Column(String)
    time    = Column(DateTime, default=datetime.now)

class Contacts(Base):
    __tablename__ = 'contacts'
    id      = Column(Integer, primary_key=True)
    name    = Column(String)
    email   = Column(String)
    comment = Column(String(6144))
    time    = Column(DateTime, default=datetime.now)
    answer  = Column(Boolean, default = False)


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id       = Column(Integer, primary_key=True)
    user     = Column(ForeignKey('users.id'))
    started  = Column(Date)
    expires  = Column(Date)
    active   = Column(Boolean, default=True)
    group    = Column(ARRAY(Integer, ForeignKey('users.id')))

