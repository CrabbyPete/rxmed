
from sqlalchemy         import ( Column,
                                 Integer, 
                                 String,
                                 or_
                               )

#from sqlalchemy.orm     import relationship
from sqlalchemy.schema  import UniqueConstraint
#from sqlalchemy.orm.exc import NoResultFound

from .base               import Base

class FTA(Base):
    __tablename__ = 'FTA'
    __table_args__ = ( UniqueConstraint('PROPRIETARY_NAME','NONPROPRIETARY_NAME'), )

    id                   = Column( Integer, primary_key= True )
    PROPRIETARY_NAME     = Column( String(255) )
    NONPROPRIETARY_NAME  = Column( String(255) )
    PHARM_CLASSES        = Column( String(255) )
    DRUG_RELASOURCE      = Column( String(255) )
    DRUG_RELA            = Column( String(255) )
    DRUG_RELASOURCE_2    = Column( String(255) )
    DRUG_RELA_2          = Column( String(255) )
    CLASS_ID             = Column( String(255) )
    EXCLUDED_DRUGS_BACK  = Column( String(255) )
    EXCLUDED_DRUGS_FRONT = Column( String(255) )
    RELATED_DRUGS        = Column( String(2054) )

    @classmethod
    def find_by_name(cls, name, nonproprietary=True ):
        """ Return an atoms by property
        """
        if not '%' in name:
            name = f"%{name.lower()}%"

        if nonproprietary:
            flter = cls.PROPRIETARY_NAME.ilike(name)
        else:
            flter = cls.PROPRIETARY_NAME.ilike(name)

        qry = cls.session.query(cls).filter( flter )
        return qry.all()

    @classmethod
    def find_nonproprietary(cls, name ):
        if not '%' in name:
            name = f"%{name.lower()}%"

        qry = cls.session.query(cls).filter( cls.NONPROPRIETARY_NAME.ilike(name) )
        return qry


    def __repr__(self):
        return "<{}>".format(self.PROPRIETARY_NAME )