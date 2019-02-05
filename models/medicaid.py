from sqlalchemy import ( Column,
                         Integer,
                         Integer,
                         String,
                         Text,
                         or_
                       )

from .base import Base


# Just return the results not the whole class
row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}


class Caresource(Base): # Drug_Name,Drug_Tier,Formulary_Restrictions
    __tablename__ = 'caresource'

    id                     = Column( Integer,  primary_key= True )
    Drug_Name              = Column(String, nullable=False )
    Drug_Tier              = Column(String)
    Formulary_Restrictions = Column(String)

    @classmethod
    def find_by_name(cls, name ):
        """
        Find the drug by its name
        :param name:
        :return:
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter(cls.Drug_Name.ilike(name)).all()
        return qry

    def __repr__(self):
        return "<{}>".format(self.Drug_Name )


class Paramount(Base): # Formulary_restriction,Generic_name,Brand_name
    __tablename__ = 'paramount'

    id                      = Column( Integer,  primary_key= True )
    Brand_name              = Column(String, nullable=False )
    Generic_name            = Column(String, nullable=False )
    Formulary_restriction   = Column(String)


    @classmethod
    def find_by_name(cls, name ):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( or_( cls.Generic_name.ilike(name),
                                                  cls.Brand_name.ilike(name)
                                                )
                                           ).all()
        return qry

    def __repr__(self):
        return "<{}>".format(self.Generic_name )


class Molina(Base): # Generic_name,Brand_name,Formulary_Restrictions
    __tablename__ = 'molina'
    id                          = Column(Integer,  primary_key= True)
    Generic_name                = Column(String, nullable=False)
    Brand_name                  = Column(String)
    Formulary_Restrictions      = Column(String)

    @classmethod
    def find_by_name(cls, name ):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( or_( cls.Generic_name.ilike(name),
                                                  cls.Brand_name.ilike(name)
                                                )
                                           ).all()
        return qry

    def __repr__(self):
        return "<{}>".format(self.DRUG_NAME )


class Molina_Healthcare( Base ): # DRUG_NAME,PA_CODE,ALTERNATIVE_DRUG_CRITERIA
    """
    class based on PLANS/Molina Healthcare PA criteria 10_1_18.csv
    """
    __tablename__ = "molinahealthcare"

    id                        = Column(Integer,  primary_key=True)
    DRUG_NAME                 = Column(String, nullable=False )
    PA_CODE                   = Column(String, nullable=False )
    ALTERNATIVE_DRUG_CRITERIA = Column(String)

    @classmethod
    def find_brand(cls, name ):
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( cls.DRUG_NAME.ilike(name) ).all()

        return qry

    def __repr__(self):
        return "<{}>".format(self.DRUG_NAME )


class UHC(Base): # Generic,Brand,Tier,Formulary_Restrictions
    __tablename__ = 'UHC'

    id                      = Column(Integer,   primary_key=True)
    Brand                   = Column(String, nullable=False)
    Generic                 = Column(String, nullable=False )
    Tier                    = Column(String)
    Formulary_Restrictions  = Column(String)

    @classmethod
    def find_by_name(cls, name ):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( or_(cls.Generic.ilike(name),
                                                 cls.Brand.ilike(name)
                                                )
                                           ).all()

        return qry


    def __repr__(self):
        return "<{}>".format(self.Generic )


class Buckeye(Base): # Drug_Name,Preferred_Agent,Fomulary_Restrictions
    __tablename__ = 'buckeye'
    id                    = Column(Integer,   primary_key=True)
    Drug_Name             = Column(String, nullable=False)
    Preferred_Agent       = Column(String, nullable=False)
    Fomulary_Restrictions = Column(String)

    @classmethod
    def find_by_name(cls, name ):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( cls.Drug_Name.ilike(name)).all()
        return qry


    def __repr__(self):
        return "<{}>".format(self.Drug_Name )
