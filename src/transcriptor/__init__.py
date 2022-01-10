from pathlib import Path

from appdirs import user_config_dir

BASE_DIR = Path("/home/kamikaze/Documents/Wera/Transcription2")
CLIENTS_FOLDER = BASE_DIR / "clients"
JOBS_FOLDER = BASE_DIR / "jobs"
WORKS_FOLDER = BASE_DIR / "work"
CONF_FOLDER = user_config_dir("transcriptor")
DATE_FMT = "%Y-%m-%d"
