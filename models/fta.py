
from sqlalchemy         import ( Column,
                                 Integer, 
                                 String,
                                 or_
                               )

from sqlalchemy.orm     import relationship
from sqlalchemy.schema  import UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound

from .base               import Base

class FTA(Base):
    __tablename__ = 'FTA'
    __table_args__ = ( UniqueConstraint('PROPRIETARY_NAME','NONPROPRIETARY_NAME'), )

    id                   = Column( Integer,     primary_key= True )
    PROPRIETARY_NAME     = Column( String(255), nullable=False )
    NONPROPRIETARY_NAME  = Column( String(255), nullable=False )
    PHARM_CLASSES        = Column( String(255), nullable=False )
    DRUG_RELASOURCE      = Column( String(255), nullable=False )
    DRUG_RELA            = Column( String(255), nullable=False )
    DRUG_RELASOURCE_2    = Column( String(255), nullable=False )
    DRUG_RELA_2          = Column( String(255), nullable=False )
    CLASS_ID             = Column( String(255), nullable=False )
    EXCLUDED_DRUGS_BACK  = Column( String(255), nullable=False )
    EXCLUDED_DRUGS_FRONT = Column( String(255), nullable=False )

    @classmethod
    def find_by_name(cls, name, nonproprietary=True ):
        """ Return an atoms by property
        """
        if not '%' in name:
            name = f"%{name.lower()}%"

        if nonproprietary:
            filter = or_( cls.PROPRIETARY_NAME.ilike(name), cls.NONPROPRIETARY_NAME.ilike(name) )
        else:
            filter = cls.PROPRIETARY_NAME.ilike(name)

        qry = cls.session.query(cls).filter( filter )
        result = qry.all()
        return result

    @classmethod
    def find_nonproprietary(cls, name ):
        if not '%' in name:
            name = f"%{name.lower()}%"

        qry = cls.session.query(cls).filter( cls.NONPROPRIETARY_NAME.ilike(name) )
        result = qry.all()
        return result


    def __repr__(self):
        return "<{}>".format(self.PROPRIETARY_NAME )