import re
import hashlib


from datetime       import datetime,date
from sqlalchemy.orm import validates
from sqlalchemy     import (Column, Boolean, Integer, String, Date,ForeignKey, ARRAY )

from .base              import Base
from sqlalchemy_utils   import EmailType

# User Profile, also used for those not signed in
class User( Base ):
    __tablename__ = 'users'

    id            = Column(Integer, primary_key=True)
    email         = Column(EmailType)
    password      = Column(String)
    title         = Column(String)
    first_name    = Column(String)
    last_name     = Column(String)
    phone         = Column(String)
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
        return self.active


    def is_anonymous(self):
        return False


    def set_password(self, raw_password):
        h = hashlib.md5()
        h.update(raw_password)
        self.password = h.hexdigest()


    def check_password(self, raw_password):
        h = hashlib.md5()
        h.update(raw_password)
        if self.password == h.hexdigest():
            return True

        return False

    def __unicode__(self):
        return f"{self.first_name} {self.last_name}"


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id       = Column(Integer, primary_key=True)
    user     = Column(ForeignKey('users.id'))
    started  = Column(Date)
    expires  = Column(Date)
    active   = Column(Boolean, default=True)
    group    = Column(ARRAY(Integer, ForeignKey('users.id')))

