from sqlalchemy import ( or_,
                         and_,
                         any_,
                         ARRAY,
                         JSON,
                         Column,
                         String,
                         Integer,
                         Boolean,
                         DECIMAL,
                         ForeignKey,
                       )

from sqlalchemy.orm     import relationship
from sqlalchemy.schema  import UniqueConstraint
from .base              import Base
from .fta               import Drugs

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
        return "{}".format(self.ZIPCODE)


class Plans(Base):
    """
    This is the Medicare plans that are paid for don't change
    """
    __tablename__ = 'plans'

    id                  = Column(Integer, primary_key= True)
    CONTRACT_ID         = Column(String)
    PLAN_ID             = Column(Integer)
    SEGMENT_ID          = Column(String)
    CONTRACT_NAME       = Column(String)
    PLAN_NAME           = Column(String)
    FORMULARY_ID        = Column(Integer)
    PREMIUM             = Column(DECIMAL(precision=8, asdecimal=True,scale=2), nullable=True)
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


class PlanNames(Base):
    __tablename__ = 'plan_names'
    __table_args__ = (UniqueConstraint('state', 'plan_name','plan_id'),)

    id         = Column(Integer, primary_key=True)
    state      = Column(String)
    plan_name  = Column(String)
    plan_id    = Column(String)
    medicaid   = Column(Boolean)
    commercial = Column(Boolean)
    source     = Column(String)

    @classmethod
    def by_state(cls, state, plan_name, medicaid):
        plan_name = f"{plan_name}%"
        fltr = and_(or_(cls.state.ilike(state), cls.state.ilike('US')),
                    cls.plan_name.ilike(plan_name),
                    cls.medicaid==medicaid
                   )
        result = cls.session.query(cls).filter(fltr)
        return result.all()

    @classmethod
    def ids_by_name(cls, state, plan_name):
        fltr = and_(or_(cls.state.ilike(state), cls.state.ilike('US')), cls.plan_name.ilike(plan_name) )
        result = cls.session.query(cls).filter(fltr)
        result = [r.id for r in result.all()]
        return result

    def __repr__(self):
        return f"{self.state}:{self.plan_name}"


# All plans based on public info
class OpenPlans(Base):
    __tablename__ = 'open_plans'
    __table_args__ = (UniqueConstraint('rxnorm_id', 'plan_id'),)

    id                  = Column(Integer, primary_key=True)
    rxnorm_id           = Column(Integer,ForeignKey('drugs.RXCUI'))
    plan_id             = Column(Integer,ForeignKey('plan_names.id'))
    quantity_limit      = Column(Boolean)
    drug_tier           = Column(String)
    step_therapy        = Column(Boolean)
    prior_authorization = Column(Boolean)
    pa_reference        = Column(String)

    drug = relationship(Drugs, primaryjoin = rxnorm_id == Drugs.RXCUI)
    plan = relationship(PlanNames, primaryjoin = plan_id == PlanNames.id)

    def __repr__(self):
        return f"{self.rxnorm_id}:{self.plan_id}"
