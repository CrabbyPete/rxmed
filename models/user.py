import re
import hashlib


from datetime       import datetime
from sqlalchemy.orm import validates
from sqlalchemy     import (Column, Boolean, Integer, String, Date )

from .base          import Base

# User Profile, also used for those not signed in
class User( Base ):
    __tablename__ = 'users'

    id          = Column( Integer, primary_key=True)
    email       = Column( String )
    password    = Column( String )
    title       = Column( String )
    first_name  = Column( String )
    last_name   = Column( String )
    joined      = Column( Date )

    # Login booleans
    active        = Column( Boolean, default = False )
    authenticated = Column( Boolean, default = False )

    @validates('email')
    def validate_email(self, key, address):
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", address):
            return address
        return False


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
        return self.email

"""
class Subscription( Document ):
    user     = ReferenceField( 'User', reverse_delete_rule = CASCADE )
    expires  = DateTimeField( default = datetime.now() )
    active   = BooleanField(default = False)

"""