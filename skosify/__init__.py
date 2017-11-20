# encoding=utf-8
from .skosify import skosify
from .config import config
from . import infer

__version__ = '1.0.0'  # Use bumpversion to update
__all__ = ['skosify', 'config', 'infer']
