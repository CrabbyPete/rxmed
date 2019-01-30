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


class Caresource(Base):
    __tablename__ = 'caresource'

    id                     = Column( Integer,  primary_key= True )
    Drug_Name              = Column( String, nullable=False )
    Drug_Tier              = Column( String, nullable=False )
    Formulary_Restrictions = Column( String, nullable=False )

    @classmethod
    def find_by_name(cls, name ):
        """
        Find the drug by its name
        :param name:
        :return:
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( cls.Drug_Name.ilike(name) )
        results = [ row2dict(r) for r  in qry ]
        return results




    def __repr__(self):
        return "<{}>".format(self.Drug_Name )


class Paramount(Base):
    __tablename__ = 'paramount'
    id                      = Column( Integer,  primary_key= True )
    Formulary_restriction   = Column( String, nullable=False )
    Generic_name            = Column( String, nullable=False )
    Brand_name              = Column( String, nullable=False )

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
                                           )
        results = [row2dict(r) for r in qry]
        return results

    def __repr__(self):
        return "<{}>".format(self.Generic_name )


class Molina(Base):
    __tablename__ = 'molina'
    id                          = Column( Integer,  primary_key= True )
    Generic_name                = Column( String, nullable=False )
    Brand_name                  = Column( String, nullable=False )
    Formulary_Restrictions       = Column( String, nullable=False )

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
                                           )
        results = [row2dict(r) for r in qry]
        return results

    def __repr__(self):
        return "<{}>".format(self.DRUG_NAME )


class Molina_Healthcare( Base ):
    """
    class based on PLANS/Molina Healthcare PA criteria 10_1_18.csv
    """
    __tablename__ = "molinahealthcare"

    id                        = Column( Integer,  primary_key=True)
    DRUG_NAME                 = Column( String, nullable=False )
    PA_CODE                   = Column( String, nullable=False )
    ALTERNATIVE_DRUG_CRITERIA = Column( String, nullable=False )

    @classmethod
    def find_brand(cls, name ):
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( cls.DRUG_NAME.ilike(name) )
        results = [row2dict(r) for r in qry]
        return results

    def __repr__(self):
        return "<{}>".format(self.DRUG_NAME )


class UHC(Base):
    __tablename__ = 'UHC'

    id                      = Column(Integer,   primary_key=True)
    Generic                 = Column( String, nullable=False )
    Brand                   = Column( String, nullable=False )
    Tier                    = Column( String, nullable=False )
    Formulary_Restrictions  = Column( String, nullable=False )

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
                                           
        results = [row2dict(r) for r in qry]
        return results


    def __repr__(self):
        return "<{}>".format(self.Generic )


class Buckeye(Base):
    __tablename__ = 'buckeye'
    id                    = Column(Integer,   primary_key=True)
    Drug_Name             = Column( String, nullable=False )
    Preferred_Agent       = Column( String, nullable=False )
    Fomulary_restriction  = Column( String, nullable=False )

    @classmethod
    def find_by_name(cls, name ):
        """
        Find similar drugs in the database
        :param name: drug name
        :return: matches
        """
        name = f"%{name.lower()}%"
        qry = cls.session.query(cls).filter( cls.Drug_Name.ilike(name))
        results = [row2dict(r) for r in qry]
        return results


    def __repr__(self):
        return "<{}>".format(self.Drug_Name )
