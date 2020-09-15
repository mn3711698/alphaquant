from aq.common.logger import log
import time
if __name__ == "__main__":
    i=1
    while True:
        log.info(f"demo {i}")
        time.sleep(5)
        i+=1