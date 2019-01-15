from sqlalchemy import ( Column,
                         Integer,
                         String,
                         Float,
                         or_
                       )

from .base      import Base


class Zipcode(Base):
    __tablename__ = 'zipcode'
    id          = Column( Integer, primary_key= True )
    ZIPCODE     = Column( String(11) )
    LATITUDE    = Column( Float )
    LONGITUDE   = Column( Float )
    CITY        = Column(String(255))
    STATE       = Column(String(255))
    STATENAME   = Column(String(255))
    COUNTY      = Column(String(255))
    ZIPCLASS    = Column(String(255))


    def __repr__(self):
        return "<{}>".format(self.ZIPCODE)


class Geolocate(Base):
    __tablename__ = 'geolocate'

    id              = Column( Integer, primary_key= True )
    COUNTY_CODE     = Column( Integer )
    STATENAME       = Column( String(255) )
    COUNTY          = Column( String(255) )
    MA_REGION_CODE  = Column( String(255) )
    MA_REGION       = Column( String(255) )
    PDP_REGION_CODE = Column( Integer )
    PDP_REGION      = Column()

    def __repr__(self):
        return "<{}-{}>".format(self.STATENAME, self.COUNTY)
