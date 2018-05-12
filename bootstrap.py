import json
import time
import os
from pymongo.errors import ConnectionFailure
from core.registry import Registry
from tools.config_creator import create_new_cfg
from tools.logger import Logger
import logging
import sys

try:

    Logger.add_logger(
        logging.handlers.RotatingFileHandler("./logs/bot.log", maxBytes=5 * 1024 * 1024 * 1024, backupCount=1000))
    Logger.add_logger(logging.StreamHandler(sys.stdout))
    Registry.logger = Logger("registry")

    logger = Logger("bootstrap")
    config_file = "./conf/config.json"

    logger.info("Starting Budabot...")
    if not os.path.exists(config_file):
        print('Configuration file not found.')
        answer = input('Would you like to create one now?[Y/n]')
        if answer == 'y' or len(answer) < 1:
            # Create a new config
            create_new_cfg()
        else:
            print(
                'You can manually create a config by editing the template /conf/config.template.json and rename it to config.json')
            exit(0)

    logger.debug("Reading config file '%s'" % config_file)
    with open(config_file) as cfg:
        config = json.load(cfg)

    logger.debug("Loading instances")
    Registry.load_instances(["core", os.path.join("modules", "core"), os.path.join("modules", "addons")])
    Registry.inject_all()

    bot = Registry.get_instance("mangopie")
    db = Registry.get_instance("db")
    db.connect(config["db_host"], config["db_name"])

    bot.init(config, Registry)
    if int(config["dimension"]) == 1:
        bot.connect("chat.d1.funcom.com", 7105)
    elif int(config["dimension"]) == 2:
        bot.connect("chat.dt.funcom.com", 7109)
    elif int(config["dimension"]) == 3:
        bot.connect("localhost", 9993)
    else:
        print('Invalid server!')
        bot.disconnect()
        time.sleep(5)
        exit(1)

    if not bot.login(config["username"], config["password"], config["character"]):
        bot.disconnect()
        time.sleep(5)
        exit(1)
    else:
        status = bot.run()
        bot.disconnect()
        exit(status.value)

except ConnectionFailure:
    print("Connection to database failed.")
    exit(1)

except KeyboardInterrupt:
    exit(0)
