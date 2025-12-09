import logging
import os
import sys
from dataclasses import dataclass
from logging import ERROR, INFO, WARNING  # for the use of the other files
from typing import List, Optional

from logs_label import LogLabel


def f(**kwargs):
    return "[" + ",".join(f"{name}={s}" for name, s in kwargs.items()) + "]"


@dataclass
class Log:
    level: str
    msg: str
    label: Optional[LogLabel]


class StoreHandler(logging.StreamHandler):

    logs: List[Log] = []

    def emit(self, record):

        self.logs.append(
            Log(
                level=record.levelname,
                msg=record.msg,
                label=record.__dict__.get("label"),
            )
        )

        return super().emit(record)


class MyLogger(logging.Logger):

    def __init__(self, name=None, level=0):
        super().__init__(name, level)

        # format
        fmt = logging.Formatter(
            fmt="- %(levelname)s: %(pathname)s:%(lineno)s\n" + "%(message)s\n"
        )

        # create handler
        hdlr = StoreHandler(stream=sys.stderr)
        hdlr.setFormatter(fmt)
        self.addHandler(hdlr)

        # level
        level = os.environ.get("LOGGER_LEVEL")
        if level:
            self.setLevel(level)

    def get_logs(self):
        return self.handlers[0].logs

    def get_logs_label(self) -> List[LogLabel]:
        return [log.label for log in self.get_logs() if log.label]

    def reset_logs(self):
        self.handlers[0].logs = []


# global logger
logger = MyLogger()


if __name__ == "__main__":
    from logs_label import EmptynessExcelCell

    logger.error("toto", extra=EmptynessExcelCell(None, None, None))
    print(logger.get_logs())
