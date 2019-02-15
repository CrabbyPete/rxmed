import pandas
import logging

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger('db.log')


class BaseMixin(object):
    """ Base class mixin to handle everything for Session
    """
    session = None

    def bulk_save(self, finish=False):
        self.bulk_buffer.append(self)
        if len(self.bulk_buffer) == 1000 or finish:
            try:
                print('saving')
                self.session.bulk_save_objects(self.bulk_buffer)
                self.session.commit()
                self.bulk_buffer.clear()
                pass

            except Exception as e:
                log.error("Database Exception {} adding ".format(str(e), self))
                self.session.rollback()

    def save(self):
        try:
            self.session.add(self)
            self.session.flush()

        except Exception as e:
            log.error("Database Exception {} adding ".format(str(e), self))
            self.session.rollback()

    def delete(self):
        self.session.delete(self)

    @classmethod
    def get(cls, id_number):
        return cls.session.query(cls).get(id_number)

    @classmethod
    def execute(cls, sql):
        try:
            result = cls.session.execute(sql)
        except Exception as e:
            cls.session.rollback()
            log.error("Database Exception {} executing {}".format(str(e), sql))
            return None
        return result

    @classmethod
    def get_or_create(cls, **kwargs):
        qry = cls.session.query(cls).filter_by(**kwargs)

        try:
            result = qry.one()
            return result

        except NoResultFound:
            return cls(**kwargs)

    @classmethod
    def get_one(cls, **kwargs):
        qry = cls.session.query(cls).filter_by(**kwargs)

        try:
            result = qry.one()
            return result

        except NoResultFound:
            return None

        except Exception as e:
            log.error("Database Exception {} for get_one {}".format(str(e), kwargs))
            cls.session.rollback()
            return None

    @classmethod
    def get_all(cls, **kwargs ):
        qry = cls.session.query(cls).filter_by(**kwargs)
        try:
            return qry.all()
        except Exception as e:
            log.error("Database Exception {} for get_all{}".format(str(e), kwargs))
            cls.session.rollback()
            return None

    @classmethod
    def query_for(cls, *args, **kwargs):
        qry = cls.session.query(*args)
        if 'order_by' in kwargs:
            qry = qry.order_by(kwargs['order_by'])
        return qry

    @classmethod
    def group_by(cls, *args, **kwargs):
        if kwargs:
            qry = cls.session.query(*args).filter_by(**kwargs).group_by(*args)
        else:
            qry = cls.session.query(*args).group_by(*args)
        return qry


Base = declarative_base(cls=BaseMixin)


class Database(object):
    """ Singleton Class to initalize the database
        Can be used as a context manager or simple open and close
    """
    bulk_buffer = []

    def __new__(cls,val):
        """
        Create a singleton
        :param val: the parameters passed in for __init__, ignore it
        :return:
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(Database, cls).__new__(cls)
        return cls.instance

    def __init__(self, url, schema='public'):
        if not 'sqlite' in url:
            self.engine = create_engine(url, echo=False, isolation_level="AUTOCOMMIT")
        else:
            self.engine = create_engine(url, echo=True, pool_recycle=3600)

        self.schema = schema


    def open(self):
        self.session = scoped_session(sessionmaker(bind=self.engine))

        Base.metadata.schema = self.schema
        Base.metadata.create_all(bind=self.engine)
        Base.session = self.session
        Base.query = self.session.query_property()
        Base.bulk_buffer = self.bulk_buffer
        return self.session


    def close(self):
        self.session.close()
        self.engine.dispose()


    def __enter__(self):
        self.open()
        return self


    def __exit__(self, type, value, traceback):
        return self.close()


    def bulk_flush(self):
        if len(self.bulk_buffer) > 0:
            try:
                self.session.bulk_save_objects(self.bulk_buffer)
                self.session.commit()
                self.bulk_buffer.clear()
            except Exception as e:
                log.error("Database Exception {} adding ".format(str(e), self))
                self.session.rollback()


    def load(self, csv_file, table, encoding = 'utf-8', sep=',', dtype=None ):
        if sep == ',':
            df = pandas.read_csv( csv_file, encoding = encoding, quoting=1 )
        else:
            df = pandas.read_csv(csv_file, sep = sep, engine='python', encoding=encoding, quoting=1)
        df.index += 1

        if dtype:
            df.to_sql(con=self.engine, index_label='id', name=table, if_exists='replace', dtype=dtype)
        else:
            df.to_sql(con=self.engine, index_label='id', name=table, if_exists='replace')
