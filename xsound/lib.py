# system packages
import os 
import sys 
import time 
import json 
import threading
import multiprocessing
import subprocess
import shutil
import yaml 
import re
import queue
import string
import random
import copy
import traceback
import datetime
import io 

# audio packages
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
import wave 
import soundfile
import kaldi_native_fbank as knf
import faster_whisper

# calculation packages
import numpy as np
import scipy
import sklearn

# web
import requests
import fastapi
import aiofiles
import asyncio