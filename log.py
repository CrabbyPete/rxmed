import sys
import logging

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('rxmedaccess')

stream_handler = logging.StreamHandler(sys.stderr)
log.addHandler(stream_handler)

file_handler = logging.FileHandler('rxmed.log')
log.addHandler( file_handler )