from configparser import ConfigParser

cf = ConfigParser()
cf.read('config.ini')

IIQ_INSTANCE = cf.get('IncidentIQ', 'Instance')
IIQ_TOKEN = cf.get('IncidentIQ', 'Token')
IIQ_SITE = cf.get('IncidentIQ', 'Site')

DATA_PATH = cf.get('General', 'Data')
LOG_PATH = cf.get('General', 'Log')
