from appdirs import user_config_dir

BASE_DIR = '/home/kamikaze/Documents/Wera/Transcription2'
CLIENT_FOLDER = BASE_DIR + '/clients'
JOB_FOLDER = BASE_DIR + '/jobs'
WORK_FOLDER = BASE_DIR + '/work'
CONF_FILE = user_config_dir('transcriptor')
DATE_FMT = '%Y-%m-%d'
