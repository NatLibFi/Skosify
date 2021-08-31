# encoding=utf-8
from .skosify import skosify
from .config import config
from . import infer, check

__version__ = '2.3.0'  # Use bumpversion to update
__all__ = ['skosify', 'config', 'infer', 'check']
