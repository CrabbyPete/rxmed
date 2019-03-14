from sqlalchemy import ( or_,
                         and_,
                         any_,
                         ARRAY,
                         Column,
                         String,
                         Integer,
                         Boolean,
                         DECIMAL,
                         ForeignKey,
                       )

from sqlalchemy.orm     import relationship
from .base              import Base

class Geolocate(Base):
    __tablename__ = 'geolocate'

    id              = Column(Integer, primary_key= True )
    COUNTY_CODE     = Column(Integer)
    STATENAME       = Column(String)
    COUNTY          = Column(String)
    MA_REGION_CODE  = Column(Integer)
    MA_REGION       = Column(String)
    PDP_REGION_CODE = Column(Integer)
    PDP_REGION      = Column(String)

    def __repr__(self):
        return "<{},{}>".format(self.STATENAME, self.COUNTY)


class Zipcode(Base):
    __tablename__ = 'zipcode'
    id          = Column(Integer, primary_key= True )
    ZIPCODE     = Column(String)
    CITY        = Column(String)
    STATE       = Column(String)
    STATENAME   = Column(String)
    COUNTY      = Column(String)
    GEO_id      = Column(Integer, ForeignKey('geolocate.id'))
    GEO         = relationship( Geolocate, primaryjoin = GEO_id == Geolocate.id)

    @classmethod
    def find_one(cls, zipcode ):
        """
        Return a simlar zipcode
        :param zipcode:
        :return:
        """
        qry = cls.session.query(cls).filter(cls.ZIPCODE.ilike(f'{zipcode}'))
        zc  = qry.one()
        return zc

    def __repr__(self):
        return "<{}>".format(self.ZIPCODE)

class Plans(Base):
    __tablename__ = 'plans'

    id                  = Column(Integer, primary_key= True)
    CONTRACT_ID         = Column(String)
    PLAN_ID             = Column(Integer)
    SEGMENT_ID          = Column(String)
    CONTRACT_NAME       = Column(String)
    PLAN_NAME           = Column(String)
    FORMULARY_ID        = Column(Integer)
    PREMIUM             = Column( DECIMAL(precision=8, asdecimal=True,scale=2), nullable=True)
    DEDUCTIBLE          = Column(DECIMAL(precision=8, asdecimal=True,scale=2), nullable=True)
    ICL                 = Column(Integer, nullable= True)
    MA_REGION_CODE      = Column(Integer)
    PDP_REGION_CODE     = Column(Integer)
    STATE               = Column(String)
    COUNTY_CODE         = Column(Integer)
    SNP                 = Column(Integer, nullable=True)
    PLAN_SUPPRESSED_YN  = Column( Boolean)
    GEO_ids             = Column( ARRAY( Integer, ForeignKey('geolocate.id')))

    @classmethod
    def find_by_formulary_id(cls, fid):
        """

        :param fid:
        :return:
        """
        qry = cls.session.query(cls).filter(cls.FORMULARY_ID == fid)
        return qry.all()

    @classmethod
    def find_by_plan_name(cls, name, exact = False, geo=None):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        if not exact:
            name = f"%{name.lower()}%"
        else:
            name = name.lower()

        fltr = cls.PLAN_NAME.ilike(name)
        if geo:
            #select * from plans where 2090 = ANY("GEO_ids");
            fltr = and_(fltr, cls.GEO_ids.any(geo))

        qry = cls.session.query(cls).filter(fltr)
        return qry.all()

    @classmethod
    def find_in_county(cls, county_code, ma_region, pdp_region, name='*'):
        """
        Query plans in a certain county
        """
        flter = or_(cls.COUNTY_CODE == county_code,
                    cls.MA_REGION_CODE == ma_region,
                    cls.PDP_REGION_CODE == pdp_region
                    )
        if not name == '*':
            look_for = f"{name.lower()}%"
            flter = and_(flter, cls.PLAN_NAME.ilike(look_for))

        qry = cls.session.query(Plans.PLAN_NAME).filter(flter).distinct(cls.PLAN_NAME).all()
        results = [r.PLAN_NAME for r in qry]
        return results

    def __repr__(self):
        return "<{}>".format(self.PLAN_NAME)


