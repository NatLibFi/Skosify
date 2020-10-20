# encoding=utf-8
from .skosify import skosify
from .config import config
from . import infer, check

__version__ = '2.1.2'  # Use bumpversion to update
__all__ = ['skosify', 'config', 'infer', 'check']
