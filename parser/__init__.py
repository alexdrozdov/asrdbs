__all__ = ['build', 'engine', 'lang', 'templates']


from common.config import configure
from parser.build.loader import new_engine
from common.config import Config


def config():
    return Config()
