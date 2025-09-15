# api & text processing deps
import pandas as pd
import numpy as np
import praw
from pprint import pprint
import json
import requests
import time
import re
import string
import os

# set env vars
APP_ID = os.getenv("REDDIT_APP_ID")
APP_SECRET = os.getenv("REDDIT_APP_SECRET")
USERNAME = os.getenv("REDDIT_USERNAME")
REDIRECT_URI = os.getenv("REDDIT_REDIRECT_URI")
APP_NAME = os.getenv("REDDIT_APP_NAME")
PASS = os.getenv("REDDIT_PASSWORD")