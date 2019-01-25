from sqlalchemy import ( Column,
                         Integer,
                         BigInteger,
                         String,
                         Text,
                         Date,
                         Boolean,
                         or_,
                         and_
                       )

from .base import Base


# Just return the results not the whole class
row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}

class NDC(Base):
    __tablename__ = 'ndc'

    id                      = Column( BigInteger, primary_key= True )
    PRODUCTID               = Column( String(2048) )
    PRODUCT_NDC             = Column( String(2048) )
    PROPRIETARY_NAME        = Column( String(2048) )
    DOSE_STRENGTH           = Column( String(2048), nullable=True )
    DOSE_UNIT               = Column( String(2048), nullable=True )
    NONPROPRIETARY_NAME     = Column( String(2048), nullable=True )
    STARTMARKETINGDATE      = Column( Date, nullable=True )
    ENDMARKETINGDATE        = Column( Date, nullable=True )
    MARKETINGCATEGORYNAME   = Column( String(2048), nullable=True )
    APPLICATIONNUMBER       = Column( String(2048), nullable=True )
    LABELERNAME             = Column( String(2048), nullable=True )
    SUBSTANCENAME           = Column( String(2048), nullable=True )
    PHARM_CLASSES           = Column( Text, nullable=True )
    DEASCHEDULE             = Column( String(2048), nullable=True )
    NDC_EXCLUDE_FLAG        = Column( String(2048), nullable=True )
    LISTING_RECORD_CERTIFIED_THROUGH = Column( String(2048), nullable=True )


    @classmethod
    def find_by_name(cls, name, nonprop=True):
        """

        :param name:
        :return:
        """
        if not '%' in name:
            name = f"%{name.lower()}%"

        if nonprop:
            flter = or_(cls.PROPRIETARY_NAME.ilike(name), cls.NONPROPRIETARY_NAME.ilike(name))
        else:
            flter = cls.PROPRIETARY_NAME.ilike(name)

        qry = cls.session.query(cls).filter(flter)
        return qry


    def __repr__(self):
        return "<{}>".format(self.PROPRIETARY_NAME)


class Plans(Base):
    __tablename__ = 'plans'

    id                  = Column( BigInteger,     primary_key= True )
    CONTRACT_ID         = Column( String(255) )
    PLAN_ID             = Column( String(255) )
    SEGMENT_ID          = Column( String(255) )
    CONTRACT_NAME       = Column( String(255) )
    PLAN_NAME           = Column( String(255) )
    FORMULARY_ID        = Column( String(255) )
    PREMIUM             = Column( String(255) )
    DEDUCTIBLE          = Column( String(255) )
    ICL                 = Column( String(255) )
    MA_REGION_CODE      = Column( String(255) )
    PDP_REGION_CODE     = Column( String(255) )
    STATE               = Column( String(255) )
    COUNTY_CODE         = Column( String(25) )
    SNP                 = Column( String(255) )
    PLAN_SUPPRESSED_YN  = Column( String(255) )

    @classmethod
    def find_by_plan_name(cls, name, exact = False ):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        if not exact:
            name = f"%{name.lower()}%"
        else:
            name = name.lower()

        qry = cls.session.query(cls).filter(cls.PLAN_NAME.ilike(name))
        results = [row2dict(r) for r in qry]
        return results

    @classmethod
    def find_in_county(cls, county_code, ma_region, pdp_region, name='*'):
        """
        Query plans in a certain county
        """
        county_code = f"%{county_code}%"
        flter = or_(cls.COUNTY_CODE.ilike(county_code),
                    cls.MA_REGION_CODE.ilike(ma_region),
                    cls.PDP_REGION_CODE == str(pdp_region)
                    )
        if not name == '*':
            look_for = f"{name.lower()}%"
            flter = and_(flter, cls.PLAN_NAME.ilike(look_for))

        qry = cls.session.query(Plans.PLAN_NAME).filter(flter).distinct(cls.PLAN_NAME).all()
        results = [r.PLAN_NAME for r in qry]
        return results

    def __repr__(self):
        return "<{}>".format(self.PLAN_NAME)


class Basic_Drugs(Base):
    __tablename__ = 'basicdrugs'

    id                      = Column( Integer, primary_key=True)
    FORMULARY_ID            = Column( String(255) )
    FORMULARY_VERSION       = Column( String(255) )
    CONTRACT_YEAR           = Column( String(10) )
    RXCUI                   = Column( String(255) )
    NDC                     = Column( Integer )
    TIER_LEVEL_VALUE        = Column( Integer )
    QUANTITY_LIMIT_YN       = Column( Boolean )
    QUANTITY_LIMIT_AMOUNT   = Column( String(255) )
    QUANTITY_LIMIT_DAYS     = Column( String(255) )
    PRIOR_AUTHORIZATION_YN  = Column( Boolean )
    STEP_THERAPY_YN         = Column( Boolean )

    @classmethod
    def get_close_to(cls, name, fid=None):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        name = f"%{name}%"
        if fid:
            qry = cls.session.query(cls).filter(cls.NDC.ilike(name), cls.FORMULARY_ID.ilike(f"%{fid}%") )
        else:
            qry = cls.session.query(cls).filter(cls.NDC.ilike(name) )

        data = qry.all()
        results = [row2dict(r) for r in data]
        return results

    def __repr__(self):
        return "<{}>".format(self.FORMULARY_ID)


class Beneficiary_Costs( Base ):
    __tablename__ = 'beneficiarycosts'

    id                          = Column( BigInteger, primary_key=True)
    CONTRACT_ID                 = Column( Text )
    PLAN_ID                     = Column( Integer )
    SEGMENT_ID                  = Column( Integer )
    COVERAGE_LEVEL              = Column( Integer )
    TIER                        = Column( Integer )
    DAYS_SUPPLY                 = Column( Integer )
    COST_TYPE_PREF              = Column( Integer )
    COST_AMT_PREF               = Column( Integer )
    COST_MIN_AMT_PREF           = Column( Integer )
    COST_MAX_AMT_PREF           = Column( Integer )
    COST_TYPE_NONPREF           = Column( Integer )
    COST_AMT_NONPREF            = Column( Integer )
    COST_MIN_AMT_NONPREF        = Column( Integer )
    COST_MAX_AMT_NONPREF        = Column( Integer )
    COST_TYPE_MAIL_PREF         = Column( Integer )
    COST_AMT_MAIL_PREF          = Column( Integer )
    COST_MIN_AMT_MAIL_PREF      = Column( Integer )
    COST_MAX_AMT_MAIL_PREF      = Column( Integer )
    COST_TYPE_MAIL_NONPREF      = Column( Integer )
    COST_AMT_MAIL_NONPREF       = Column( Integer )
    COST_MIN_AMT_MAIL_NONPREF   = Column( Integer )
    COST_MAX_AMT_MAIL_NONPREF   = Column( Integer )
    TIER_SPECIALTY_YN           = Column( Text )
    DED_APPLIES_YN              = Column( Text )
    GAP_COV_TIER                = Column( Integer )

    def __repr__(self):
        return "<{}-{}>".format(self.CONTRACT_ID, self.PLAN_ID)
