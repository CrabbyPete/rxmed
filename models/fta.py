
from datetime           import date
from sqlalchemy         import ( Column,
                                 Integer,
                                 Date,
                                 String,
                                 Boolean,
                                 ForeignKey,
                                 ARRAY,
                                 JSON,
                                 or_,
                               )

from sqlalchemy.orm     import relationship
from sqlalchemy.schema  import UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound

from .base               import Base


class OpenNDC(Base):
    __tablename__ ='open_ndc'
    id = Column(Integer, primary_key=True)
    product_ndc         = Column(String)
    brand_name          = Column(String)
    brand_name_base     = Column(String)
    product_type        = Column(String)
    route               = Column(ARRAY(String))
    generic_name        = Column(String)
    rxcui               = Column(ARRAY(Integer))
    pharm_class         = Column(ARRAY(String))
    packaging           = Column(JSON)
    active_ingredients  = Column(JSON)

    @classmethod
    def find_by_rxcui(cls, rxcui):
        qry = cls.session.query(cls).filter(cls.rxcui.any(rxcui))
        return qry.all()

    @classmethod
    def find_by_name(cls, proprietary, nonproprietary=None):
        """

        :param name:
        :return:
        """
        if ' ' in proprietary:
            proprietary = proprietary.split()[0]

        proprietary = f"{proprietary.lower()}%"
        if nonproprietary is None:
            flter = or_(cls.brand_name.ilike(proprietary), cls.generic_name.ilike(proprietary))
        else:
            nonpropietary = f"%{nonproprietary.lower()}%"
            flter = or_(cls.generic_name.ilike(proprietary),cls.generic_name.ilike(nonproprietary))

        qry = cls.session.query(cls).filter(flter)
        result = qry.all()
        return result



class NDC(Base):
    __tablename__ = 'ndc'

    id                      = Column(Integer, primary_key= True)
    PRODUCTID               = Column(String)
    PRODUCT_NDC             = Column(String)
    PROPRIETARY_NAME        = Column(String)
    DOSE_STRENGTH           = Column(String, nullable=True)
    DOSE_UNIT               = Column(String, nullable=True)
    NONPROPRIETARY_NAME     = Column(String, nullable=True)
    STARTMARKETINGDATE      = Column(Date,   nullable=True)
    ENDMARKETINGDATE        = Column(Date,   nullable=True)
    MARKETINGCATEGORYNAME   = Column(String, nullable=True)
    APPLICATIONNUMBER       = Column(String, nullable=True)
    LABELERNAME             = Column(String, nullable=True)
    SUBSTANCENAME           = Column(String, nullable=True)
    PHARM_CLASSES           = Column(String, nullable=True)
    DEASCHEDULE             = Column(String, nullable=True)
    NDC_EXCLUDE_FLAG        = Column(String, nullable=True)
    RXCUI                   = Column(Integer, nullable=True)
    LISTING_RECORD_CERTIFIED_THROUGH = Column(String, nullable=True)

    @classmethod
    def find_similar(cls, ndc, cache=None):
        """
        Transpose an Basic Drug NDC to an NDC
        :param ndc: basic drug format ndc
        :return:
        """
        #Drop the last 2 number
        ndc = ndc[:-2]
        ndc = f"%{ndc[1:-4]}-{ndc[-4:]}%"
        if not cache is None and ndc in cache:
            return cache[ndc]

        qry = cls.session.query(cls).filter(cls.PRODUCT_NDC.ilike(ndc))
        try:
            result = qry.one()
        except:
            return None

        if not cache is None:
            cache[ndc]=result
        return result

    @classmethod
    def find_by_name(cls, proprietary, nonproprietary=None):
        """

        :param name:
        :return:
        """
        if ' ' in proprietary:
            proprietary = proprietary.split()[0]

        proprietary = f"{proprietary.lower()}%"
        if nonproprietary is None:
            flter = or_(cls.PROPRIETARY_NAME.ilike(proprietary), cls.NONPROPRIETARY_NAME.ilike(proprietary))
        else:
            nonpropietary = f"%{nonproprietary.lower()}%"
            flter = or_(cls.PROPRIETARY_NAME.ilike(proprietary),cls.NONPROPRIETARY_NAME.ilike(nonproprietary))

        qry = cls.session.query(cls).filter(flter)
        result = qry.all()
        return result


    def __repr__(self):
        return "<{}>".format(self.PROPRIETARY_NAME)


class Drugs(Base):
    __tablename__ = 'drugs'

    id                   = Column(Integer, primary_key=True)
    RXCUI                = Column(Integer)
    TTY                  = Column(String)
    NAME                 = Column(String)
    RELASOURCE           = Column(String)
    RELA                 = Column(String)
    CLASS_ID             = Column(String)
    CLASS_NAME           = Column(String)


class FTA(Base):
    __tablename__ = 'fta'
    __table_args__ = (UniqueConstraint('PROPRIETARY_NAME','NONPROPRIETARY_NAME'),)

    id                   = Column(Integer, primary_key= True)
    PROPRIETARY_NAME     = Column(String)
    NONPROPRIETARY_NAME  = Column(String)
    PHARM_CLASSES        = Column(String)
    DRUG_RELASOURCE      = Column(String)
    DRUG_RELA            = Column(String)
    EXCLUDED_DRUGS_BACK  = Column(String)
    EXCLUDED_DRUGS_FRONT = Column(String)
    RELATED_DRUGS        = Column(ARRAY(Integer, ForeignKey('fta.id')))
    ACTIVE               = Column(Boolean, default=True)
    MODIFIED             = Column(Date, default=date.today)
    RXCUI                = Column(Integer)
    TTY                  = Column(String)
    CLASS_ID             = Column(String)
    CLASS_NAME           = Column(String)
    SBD_RXCUI            = Column(ARRAY(Integer))

    @classmethod
    def find_by_name(cls, name, nonproprietary=True ):
        """ Return an atoms by property
        """
        if not '%' in name:
            name = f"{name.lower().split()[0]}%"

        if nonproprietary:
            flter = or_(cls.PROPRIETARY_NAME.ilike(name), cls.NONPROPRIETARY_NAME.ilike(name) )
        else:
            flter = cls.PROPRIETARY_NAME.ilike(name)

        qry = cls.session.query(cls).filter( flter )
        return qry.all()

    @classmethod
    def find_nonproprietary(cls, name ):
        if not '%' in name:
            name = f"%{name.lower()}%"

        qry = cls.session.query(cls).filter( cls.NONPROPRIETARY_NAME.ilike(name) )
        return qry.all()

    @classmethod
    def find_rxcui(cls,rxcui):
        qry = cls.session.query(cls).filter( cls.RXCUI == rxcui)
        return qry.all()

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.PROPRIETARY_NAME )






