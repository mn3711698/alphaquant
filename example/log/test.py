from aq.common.logger import log
from aq.engine.mqevent import Event
from aq.data.market import Market

def callback(ch, method, properties, data):
    print(data)



if __name__ == "__main__":
        Market("log","Alpha.*","*",callback)

