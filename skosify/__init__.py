# encoding=utf-8
from .skosify import Skosify
from .config import Config

__version__ = '1.0.0'  # Use bumpversion to update


def skosify(*sources, **config):
    """Wraps internal calling syntax."""
    return Skosify().skosify(*sources, **config)


def config(filename=None):
    """Get default configuration and optional settings from config file."""
    return vars(Config(filename))
