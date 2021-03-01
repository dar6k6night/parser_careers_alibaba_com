import configparser
import inspect
import os

conf = configparser.RawConfigParser()
dirname = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

conf.read(dirname+'/conf.ini')
try:
    #DRIVER
    drv = conf.get("DRIVER", "drv")
    disable_images = conf.get("DRIVER", "disable_images")
    implicitly_wait = int(conf.get("DRIVER", "implicitly_wait"))
    driver_delay = int(conf.get("DRIVER", "driver_delay"))
    headless=conf.get("DRIVER", "headless")
    user_agent=conf.get("DRIVER", "user_agent")

    #BASE
    db_path = conf.get("BASE", "path")

    #MiSC
    try:
        max_repeat = int(conf.get("MISC", "max_repeat"))
    except :
        max_repeat = 1

except:
    print("Error in conf.ini...")
    input("Enter for exit...")
    exit(0)
