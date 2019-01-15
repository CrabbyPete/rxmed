from sqlalchemy import ( Column,
                         Integer,
                         String,
                         or_
                       )

from .base import Base


# Just return the results not the whole class
row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}

class Caresource(Base):
    __tablename__ = 'caresource'

    id                     = Column( Integer,     primary_key= True )
    Drug_Name              = Column( String(255), nullable=False )
    Drug_Tier              = Column( String(255), nullable=False )
    Formulary_Restrictions = Column( String(255), nullable=False )

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
    id                      = Column( Integer,     primary_key= True )
    Formulary_restriction   = Column( String(255), nullable=False )
    Generic_name            = Column( String(255), nullable=False )
    Brand_name              = Column( String(255), nullable=False )

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
    id                          = Column( Integer,     primary_key= True )
    Generic_name                = Column( String(255), nullable=False )
    Brand_name                  = Column( String(255), nullable=False )
    Formulary_restriction       = Column( String(255), nullable=False )

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

    id                        = Column( Integer, primary_key=True)
    DRUG_NAME                 = Column( String(255), nullable=False )
    PA_CODE                   = Column( String(255), nullable=False )
    ALTERNATIVE_DRUG_CRITERIA = Column( String(255), nullable=False )

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

    id                      = Column(Integer, primary_key=True)
    Generic                 = Column( String(255), nullable=False )
    Brand                   = Column( String(255), nullable=False )
    Tier                    = Column( String(255), nullable=False )
    Formulary_Restriction   = Column( String(255), nullable=False )

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
                                           )
        results = [row2dict(r) for r in qry]
        return results


    def __repr__(self):
        return "<{}>".format(self.Generic )


class Buckeye(Base):
    __tablename__ = 'buckeye'
    id                   = Column(Integer, primary_key=True)
    Drug_Name            = Column( String(255), nullable=False )
    Preferred_Agent      = Column( String(255), nullable=False )
    Fomulary_restriction = Column( String(255), nullable=False )

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
