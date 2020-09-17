import os,sys
baseroot = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/alphaquant/')
import logging
from logging.handlers import TimedRotatingFileHandler
import platform

from  aq.common.tools  import *
import logging
from python_logging_rabbitmq import RabbitMQHandler

from aq.data.MongoDataSerer import db
import traceback
from aq.common.tools import *
import json
from  aq.engine.config import config

path = os.path.split(os.path.realpath(__file__))[0]
log_path = os.path.join(path, 'result')  # 存放log文件的路径




# now we patch Python code to add color support to logging.StreamHandler
def add_coloring_to_emit_windows(fn):
    # add methods we need to the class
    def _out_handle(self):
        import ctypes
        return ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)

    out_handle = property(_out_handle)

    def _set_color(self, code):
        import ctypes
        # Constants from the Windows API
        self.STD_OUTPUT_HANDLE = -11
        hdl = ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        ctypes.windll.kernel32.SetConsoleTextAttribute(hdl, code)

    setattr(logging.StreamHandler, '_set_color', _set_color)

    def new(*args):
        FOREGROUND_BLUE = 0x0001  # text color contains blue.
        FOREGROUND_GREEN = 0x0002  # text color contains green.
        FOREGROUND_RED = 0x0004  # text color contains red.
        FOREGROUND_INTENSITY = 0x0008  # text color is intensified.
        FOREGROUND_WHITE = FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED
        # winbase.h
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        # wincon.h
        FOREGROUND_BLACK = 0x0000
        FOREGROUND_BLUE = 0x0001
        FOREGROUND_GREEN = 0x0002
        FOREGROUND_CYAN = 0x0003
        FOREGROUND_RED = 0x0004
        FOREGROUND_MAGENTA = 0x0005
        FOREGROUND_YELLOW = 0x0006
        FOREGROUND_GREY = 0x0007
        FOREGROUND_INTENSITY = 0x0008  # foreground color is intensified.

        BACKGROUND_BLACK = 0x0000
        BACKGROUND_BLUE = 0x0010
        BACKGROUND_GREEN = 0x0020
        BACKGROUND_CYAN = 0x0030
        BACKGROUND_RED = 0x0040
        BACKGROUND_MAGENTA = 0x0050
        BACKGROUND_YELLOW = 0x0060
        BACKGROUND_GREY = 0x0070
        BACKGROUND_INTENSITY = 0x0080  # background color is intensified.

        levelno = args[1].levelno
        if (levelno >= 50):
            color = BACKGROUND_YELLOW | FOREGROUND_RED | FOREGROUND_INTENSITY | BACKGROUND_INTENSITY
        elif (levelno >= 40):
            color = FOREGROUND_RED | FOREGROUND_INTENSITY
        elif (levelno >= 30):
            color = FOREGROUND_YELLOW | FOREGROUND_INTENSITY
        elif (levelno >= 20):
            color = FOREGROUND_GREEN
        elif (levelno >= 10):
            color = FOREGROUND_MAGENTA
        else:
            color = FOREGROUND_WHITE
        args[0]._set_color(color)

        ret = fn(*args)
        args[0]._set_color(FOREGROUND_WHITE)
        # print "after"
        return ret

    return new


def add_coloring_to_emit_ansi(fn):
    # add methods we need to the class
    def new(*args):
        levelno = args[1].levelno
        if (levelno >= 50):
            color = '\x1b[31m'  # red
        elif (levelno >= 40):
            color = '\x1b[31m'  # red
        elif (levelno >= 30):
            color = '\x1b[33m'  # yellow
        elif (levelno >= 20):
            color = '\x1b[32m'  # green
        elif (levelno >= 10):
            color = '\x1b[35m'  # pink
        else:
            color = '\x1b[0m'  # normal
        try:
            args[1].msg = color + args[1].msg + '\x1b[0m'  # normal
        except Exception as e:
            pass
        # print "after"
        return fn(*args)

    return new


class Logger(object):
    def __init__(self, logger_name=None):
        # 日志输出格式
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        filename = sys.argv[0]
        filename = os.path.basename(filename)
        filename, x = os.path.splitext(filename)
        if not logger_name:
            logger_name="Alpha."+filename

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        rabbit = RabbitMQHandler(host=config.rabbitmq.host, port=config.rabbitmq.port)
        self.logger.addHandler(rabbit)
        logging.root.setLevel(logging.NOTSET)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """在logger中添加日志句柄并返回，如果logger已有句柄，则直接返回"""
        return self.logger

log=Logger().get_logger()
def callback(ch, method, properties, data):
    try:
        data=data.decode("utf8")
        data=json.loads(data)
        data["time"]=get_cur_datetime_m()
        db.insert_one("log",data)#存入数据库
        msg=data['msg']
        t=data["created"]
        t=ts_to_datetime_str(round(t*1000))
        name=data["name"]
        level=data["levelname"]
        print(f"{t} -{name} - {level} -{msg} ")
    except Exception as e:
        print(e)
        traceback.print_exc()

if __name__ == "__main__":
    from aq.data.market import Market
    Market("log","Alpha.*","*",callback)