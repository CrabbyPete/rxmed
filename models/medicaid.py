from datetime           import datetime,date

from sqlalchemy         import Column, Integer, String, Date, DateTime, Boolean, DECIMAL, or_
from sqlalchemy_utils   import URLType

from .base              import Base
from .fta               import Drugs

# Just return the results not the whole class
row2dict = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns}

class OhioState(Base):
    __tablename__ = 'ohiostate'

    id                              = Column(Integer, primary_key=True)
    drug_name                       = Column(String)
    Product_Description             = Column(String)
    Prior_Authorization_Required    = Column(String)
    Copay                           = Column(String)
    Package                         = Column(String)
    Covered_for_Dual_Eligible       = Column(String)
    Route_of_Administration         = Column(String)
    PA_Reference                    = Column(URLType)
    RXCUI                           = Column(Integer)
    TTY                             = Column(String)
    modified                        = Column(Date, default=date.today)
    active                          = Column(Boolean, default=True)
    data                            = Column(Date, default=date.today)

    @classmethod
    def find_product(cls, name):
        name = f'{name.split()[0].lower()}%'
        qry = cls.session.query(cls).filter(cls.drug_name.ilike(name))
        results = qry.all()
        return [row2dict(r) for r in results]

    @classmethod
    def find_by_rxcui(cls, rxcui):
        qry = cls.session.query(cls).filter(cls.RXCUI == rxcui)
        return qry.all()