# app/core/loging.py

import logging, sys, json
from datetime import datetime
from core.config import settings

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "logger": record.name,
            "level": record.levelname,
            "msg": record.getMessage(),
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)

def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL)
