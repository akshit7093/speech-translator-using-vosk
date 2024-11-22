import os
import sys

if getattr(sys, 'frozen', False):
    os.environ['PYTORCH_JIT'] = '0'
