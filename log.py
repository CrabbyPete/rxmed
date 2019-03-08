import os
import sys
import inspect
import logging

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('rxmedaccess')

fmt = logging.Formatter('%(asctime)s-%(message)s')


stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(fmt)

log.addHandler(stream_handler)

file_handler = logging.FileHandler('rxmed.log')
file_handler.setFormatter(fmt)
log.addHandler( file_handler )


rq_log = logging.getLogger(__name__)
file_handler = logging.FileHandler('requests.log')
file_handler.setFormatter(fmt)
rq_log.addHandler( file_handler )


def log_msg( msg ):
    stack = inspect.stack()[1]
    file = os.path.basename( stack[1] ) 
    msg =  '{} in {} line:{}'.format (msg, file, stack[2] )
    return msg 