from sqlalchemy import ( Column,
                         Integer,
                         String,
                         Float,
                         ForeignKey,
        
                       )

from sqlalchemy.orm     import relationship
from .base              import Base

class Geolocate(Base):
    __tablename__ = 'geolocate'

    id              = Column( Integer, primary_key= True )
    COUNTY_CODE     = Column( Integer )
    STATENAME       = Column( String(255) )
    COUNTY          = Column( String(255) )
    MA_REGION_CODE  = Column( String(255) )
    MA_REGION       = Column( String(255) )
    PDP_REGION_CODE = Column( Integer )
    PDP_REGION      = Column( String(255) )

    def __repr__(self):
        return "<{}-{}>".format(self.STATENAME, self.COUNTY)


class Zipcode(Base):
    __tablename__ = 'zipcode'
    id          = Column( Integer, primary_key= True )
    ZIPCODE     = Column( String(11) )
    CITY        = Column(String(255), nullable=True)
    STATE       = Column(String(255), nullable=True)
    STATENAME   = Column(String(255))
    COUNTY      = Column(String(255))
    ZIPCLASS    = Column(String(255), nullable=True)
    GEO_id      = Column( Integer, ForeignKey('geolocate.id') )
    
    GEO         = relationship( Geolocate, primaryjoin = GEO_id == Geolocate.id )

    @classmethod
    def find_one(cls, zipcode ):
        """
        Return a simlar zipcode
        :param zipcode:
        :return:
        """
        while zipcode.startswith('0'):
            zipcode = zipcode[1:]
        qry = cls.session.query(cls).filter(cls.ZIPCODE.ilike(f'{zipcode}'))
        zc  = qry.one()
        return zc

    def __repr__(self):
        return "<{}>".format(self.ZIPCODE)

