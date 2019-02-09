
from sqlalchemy         import ( Column,
                                 Integer, 
                                 String,
                                 ForeignKey,
                                 Date,
                                 ARRAY,
                                 Boolean,
                                 or_,
                                 and_
                               )

from sqlalchemy.orm     import relationship
from sqlalchemy.schema  import UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound

from .base               import Base

class NDC(Base):
    __tablename__ = 'ndc'

    id                      = Column( Integer, primary_key= True )
    PRODUCTID               = Column( String )
    PRODUCT_NDC             = Column( String )
    PROPRIETARY_NAME        = Column( String )
    DOSE_STRENGTH           = Column( String, nullable=True )
    DOSE_UNIT               = Column( String, nullable=True )
    NONPROPRIETARY_NAME     = Column( String, nullable=True )
    STARTMARKETINGDATE      = Column( Date,   nullable=True )
    ENDMARKETINGDATE        = Column( Date,   nullable=True )
    MARKETINGCATEGORYNAME   = Column( String, nullable=True )
    APPLICATIONNUMBER       = Column( String, nullable=True )
    LABELERNAME             = Column( String, nullable=True )
    SUBSTANCENAME           = Column( String, nullable=True )
    PHARM_CLASSES           = Column( String, nullable=True )
    DEASCHEDULE             = Column( String, nullable=True )
    NDC_EXCLUDE_FLAG        = Column( String, nullable=True )
    LISTING_RECORD_CERTIFIED_THROUGH = Column( String, nullable=True )


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
        proprietary = f"%{proprietary.lower()}%"
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


class FTA(Base):
    __tablename__ = 'fta'
    __table_args__ = (UniqueConstraint('PROPRIETARY_NAME','NONPROPRIETARY_NAME'),)

    id                   = Column( Integer, primary_key= True )
    PROPRIETARY_NAME     = Column( String )
    NONPROPRIETARY_NAME  = Column( String )
    PHARM_CLASSES        = Column( String )
    DRUG_RELASOURCE      = Column( String )
    DRUG_RELA            = Column( String )
    DRUG_RELASOURCE_2    = Column( String )
    DRUG_RELA_2          = Column( String )
    CLASS_ID             = Column( String )
    EXCLUDED_DRUGS_BACK  = Column( String )
    EXCLUDED_DRUGS_FRONT = Column( String )

    RELATED_DRUGS        = Column( ARRAY(Integer, ForeignKey('fta.id')))
    NDC_IDS              = Column( ARRAY(Integer, ForeignKey('ndc.id')))

    @classmethod
    def find_by_name(cls, name, nonproprietary=True ):
        """ Return an atoms by property
        """
        if not '%' in name:
            name = f"%{name.lower()}%"

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


    def __repr__(self):
        return "<{}:{}>".format(self.id, self.PROPRIETARY_NAME )
