
import os, sys
# os.chdir('dev')
# print('cwd ', os.getcwd())

# import init

try:
    import dev.logging2 as logging
except:
    import logging2 as logging  # python windows ?

print()
print('##### Simple ####')
print()


logging.debug("test - debug")  # ignored by default
logging.info("test - info")  # ignored by default
logging.warning("test - warning")
logging.error("test - error")
logging.critical("test - critical")
print()

print('### Params ###')
print()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("test")
log.debug("Test message: %d(%s)", 100, "foobar")
log.info("Test message2: %d(%s)", 100, "foobar")
log.warning("Test message3: %d(%s)")
log.error("Test message4")
log.critical("Test message5")
logging.info("Test message6")

try:
    1 / 0
except:
    log.exception("Some trouble (%s)", "expected")


class MyHandler(logging.Handler):
    def emit(self, record):
        print("levelname=%(levelname)s name=%(name)s message=%(message)s" % record.__dict__)


logging.getLogger().addHandler(MyHandler())
logging.info("Test message7")
print()

print('#### Formatter #####')
print()
import logging2

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# Create file handler and set level to error
file_handler = logging.FileHandler("error.log", mode="w")
file_handler.setLevel(logging.ERROR)

# Create a formatter
formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s")

# Add formatter to the handlers
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# Log some messages
logger.debug("debug message")
logger.info("info message")
logger.warning("warn message")
logger.error("error message")
logger.critical("critical message")
logger.info("message %s %d", "arg", 5)
logger.info("message %(foo)s %(bar)s", {"foo": 1, "bar": 20})

try:
    1 / 0
except:
    logger.error("Some trouble (%s)", "expected")


# Custom handler example
class MyHandler(logging.Handler):
    def emit(self, record):
        print("levelname=%(levelname)s name=%(name)s message=%(message)s" % record.__dict__)


logging.getLogger().addHandler(MyHandler())
logging.info("Test message7")

print()
print('#### Root Logger ####')
print()

import logging2, sys

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter("[%(levelname)s]:%(name)s:%(message)s"))
logging.info("hello upy")
logging.getLogger("child").info("hello 2")
logging.getLogger("child").debug("hello 2")



