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
import zipfile
from io import BytesIO
from scipy import spatial
from dotenv import load_dotenv

# initialize env vars from .envrc
load_dotenv(os.path.abspath('..') + '/.envrc', verbose = False)

# set env vars
APP_ID = os.environ.get("REDDIT_APP_ID")
APP_SECRET = os.environ.get("REDDIT_APP_SECRET")
USERNAME = os.environ.get("REDDIT_USERNAME")
REDIRECT_URI = os.environ.get("REDDIT_REDIRECT_URI")
APP_NAME = os.environ.get("REDDIT_APP_NAME")
PASS = os.environ.get("REDDIT_PASSWORD")

# praw auth
reddit = praw.Reddit(
    client_id = APP_ID,
    client_secret = APP_SECRET,
    user_agent = USERNAME,
    check_for_async = False)

# requests auth
client_auth = requests.auth.HTTPBasicAuth(APP_ID, APP_SECRET)
post_data = {"grant_type": "password", "username": USERNAME,
             "password": PASS}
headers = {"User-Agent": '{} by {}'.format(APP_NAME, USERNAME)}
print(client_auth)
print(headers)
auth_response = requests.post("https://www.reddit.com/api/v1/access_token",
                              auth=client_auth, data=post_data, headers=headers)
pprint(auth_response.json())

# save access token
# print(auth_response.status_code)
if auth_response.status_code == 200:
  TOKEN = auth_response.json()['access_token']

# find extra reddit search terms using GLoVe
glove_zip_url = 'https://nlp.stanford.edu/data/wordvecs/glove.2024.wikigiga.50d.zip'
glove_zip_response = requests.get(glove_zip_url)
glove_zip = zipfile.ZipFile(BytesIO(glove_zip_response.content))
unzip_path = './data/glove/'
glove_zip.extractall(unzip_path)
del glove_zip_response, glove_zip
glove_vector_path = unzip_path + os.listdir(unzip_path)[0]

# load glove vectors & find search terms
embeddings_dict = {}
with open(glove_vector_path, 'r') as f:
   for line in f:
    values = line.split(' ')
    word = values[0]
    vector = np.asarray(values[1:], dtype = 'float32')
    embeddings_dict[word] = vector
# add search terms if needed and use below code for ideas
search_terms = ['nutrition', 'diet', 'gut', 'digestion', 'food', 'supplement', 'vegetarian', 'health']
def find_closest_embeddings(embedding):
   return sorted(embeddings_dict.keys(), key=lambda word: spatial.distance.euclidean(embeddings_dict[word], embedding))
for term in search_terms:
   closest_embeddings = find_closest_embeddings(embeddings_dict[term])[1:10]
   print(f"Closest terms to {term}:")
   print(closest_embeddings)

# delete glove vectors to free space
os.remove(glove_vector_path)
os.rmdir(unzip_path)