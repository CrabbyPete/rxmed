
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


class Drugs(Base):
    __tablename__ = 'drugs'

    RXCUI                = Column(Integer, primary_key=True)
    TTY                  = Column(String)
    NAME                 = Column(String)
    CLASS_ID             = Column(ARRAY(String))

    def __repr__(self):
        return self.NAME


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
    SCD                  = Column(ARRAY(Integer))
    SBD                  = Column(ARRAY(Integer))

    @classmethod
    def find_by_name(cls, name, nonproprietary=True ):
        """ Return an atoms by property
        """
        if not '%' in name:
            try:
                name = f"{name.lower().split()[0]}%"
            except IndexError:
                if len(name)>4:
                    name = f"{name}%"


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






