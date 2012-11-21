
from ConfigParser import ConfigParser


config = ConfigParser()

def get_config(section, key):
    return config.get(section, key)
