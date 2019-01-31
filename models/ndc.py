from sqlalchemy         import ( Column,
                                ARRAY,
                                Integer,
                                DECIMAL,
                                String,
                                Text,
                                Date,
                                Boolean,
                                ForeignKey,
                                or_,
                                and_
                              )
from sqlalchemy.orm     import relationship

from .base              import Base

# Just return the results not the whole class
row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


class Basic_Drugs(Base):
    __tablename__ = 'basicdrugs'

    id                      = Column( Integer, primary_key=True)
    FORMULARY_ID            = Column( Integer )
    FORMULARY_VERSION       = Column( String )
    CONTRACT_YEAR           = Column( Date )
    RXCUI                   = Column( Integer )
    NDC                     = Column( String )
    TIER_LEVEL_VALUE        = Column( Integer )
    QUANTITY_LIMIT_YN       = Column( Boolean )
    QUANTITY_LIMIT_AMOUNT   = Column( Integer, nullable=True )
    QUANTITY_LIMIT_DAYS     = Column( Integer, nullable=True )
    PRIOR_AUTHORIZATION_YN  = Column( Boolean )
    STEP_THERAPY_YN         = Column( Boolean )
    NDC_id                  = Column(Integer, ForeignKey('ndc.id'))


    @classmethod
    def get_close_to(cls, ndc_number, fid=None):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        ndc_number =  int( ndc_number.replace("-","") )
        ndc = f"%{ndc_number}%"
        if fid:
            qry = cls.session.query(cls).filter(cls.NDC.ilike(ndc), cls.FORMULARY_ID == fid )
        else:
            qry = cls.session.query(cls).filter(cls.NDC.ilike(ndc) )

        data = qry.all()
        results = [row2dict(r) for r in data]
        return results

    def __repr__(self):
        return "<{}>".format(self.FORMULARY_ID)


class Beneficiary_Costs( Base ):
    __tablename__ = 'beneficiarycosts'

    id                          = Column( Integer, primary_key=True)
    CONTRACT_ID                 = Column( String )
    PLAN_ID                     = Column( Integer )
    SEGMENT_ID                  = Column( Integer )
    COVERAGE_LEVEL              = Column( Integer )
    TIER                        = Column( Integer )
    DAYS_SUPPLY                 = Column( Integer )
    COST_TYPE_PREF              = Column( Integer )
    COST_AMT_PREF               = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MIN_AMT_PREF           = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MAX_AMT_PREF           = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_TYPE_NONPREF           = Column( Integer )
    COST_AMT_NONPREF            = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MIN_AMT_NONPREF        = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MAX_AMT_NONPREF        = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_TYPE_MAIL_PREF         = Column( Integer )
    COST_AMT_MAIL_PREF          = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MIN_AMT_MAIL_PREF      = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MAX_AMT_MAIL_PREF      = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_TYPE_MAIL_NONPREF      = Column( Integer )
    COST_AMT_MAIL_NONPREF       = Column( Integer )
    COST_MIN_AMT_MAIL_NONPREF   = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    COST_MAX_AMT_MAIL_NONPREF   = Column( DECIMAL(precision=8,asdecimal=True,scale=2), nullable=True)
    TIER_SPECIALTY_YN           = Column( Boolean )
    DED_APPLIES_YN              = Column( Boolean )
    GAP_COV_TIER                = Column( Integer )

    def __repr__(self):
        return "<{}-{}>".format(self.CONTRACT_ID, self.PLAN_ID)
