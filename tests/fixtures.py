
import json
import glob
import inspect
import os.path

import models

from datetime import datetime, timedelta

def load_fixtures( path, files ):
    """ Load test data from json file into the table with the same name
    """

    # Get all the class names from models
    table = {}
    for name, base in inspect.getmembers( models, inspect.isclass ):
        if not hasattr( base, '__table__' ):
            continue
        
        table[ base.__tablename__ ] = base
    
    for fyl in files:
        
        try:
            fn = os.path.join( path, fyl )
        except:
            continue
        else:
            base = fyl.split('.')[0]
            with open(fn) as f:
                while True:
                    row = f.readline().replace( '\n', '' )
                    if not row:
                        break
                    try:
                        row = json.loads( row )
                    except Exception as e:
                        pass

                    if 'modified' in row:
                        if not row['modified']:
                            row['modified'] = datetime.today() - timedelta(days = 1)
                        else:
                            row['modified'] = datetime.strptime(row['date'], "%Y-%m-%d" )

                    for r in row:
                        record = table[base]( **r )
                        record.save()
                
if __name__ == '__main__':
    from models import Database
    
    with Database('sqlite:///'):
        load_fixtures("fixtures/", ['fta.json'])
    
    