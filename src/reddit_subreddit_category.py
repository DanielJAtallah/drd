# api & text processing deps
import praw
from pprint import pprint
import requests
import os
from dotenv import load_dotenv
from search_term_explorer import NewSearchTermExplorer
from candidate_reviewer import CandidateReviewer
from tqdm import tqdm

# initialize env vars from .envrc
load_dotenv(os.path.abspath("..") + "/.envrc", verbose=False)

# set env vars
APP_ID = os.environ.get("REDDIT_APP_ID")
APP_SECRET = os.environ.get("REDDIT_APP_SECRET")
USERNAME = os.environ.get("REDDIT_USERNAME")
REDIRECT_URI = os.environ.get("REDDIT_REDIRECT_URI")
APP_NAME = os.environ.get("REDDIT_APP_NAME")
PASS = os.environ.get("REDDIT_PASSWORD")

# praw auth
reddit = praw.Reddit(
    client_id=APP_ID,
    client_secret=APP_SECRET,
    user_agent=USERNAME,
    check_for_async=False,
)

# requests auth
client_auth = requests.auth.HTTPBasicAuth(APP_ID, APP_SECRET)
post_data = {"grant_type": "password", "username": USERNAME, "password": PASS}
headers = {"User-Agent": "{} by {}".format(APP_NAME, USERNAME)}
print(client_auth)
print(headers)
auth_response = requests.post(
    "https://www.reddit.com/api/v1/access_token",
    auth=client_auth,
    data=post_data,
    headers=headers,
)
pprint(auth_response.json())

# save access token
# print(auth_response.status_code)
if auth_response.status_code == 200:
    TOKEN = auth_response.json()["access_token"]

# find extra reddit search terms using GLoVe
search_terms = [
    "nutrition",
    "diet",
    "gut",
    "digestion",
    "food",
    "supplement",
    "health",
    "cibo",
    "microbiome",
    "probiotic",
    "prebiotic",
    "plant-based",
    "fiber",
    "vitamin",
    "autoimmunemetabolism",
    "intolerance",
    "ibs",
    "celiac",
    "allergy",
    "inflammation",
    "bloating",
]
glove_ingest = input(
    "Do you want to explore new search terms with GLoVe vectors? (y/n): "
)
if glove_ingest.lower() != "y":
    print("Skipping GLoVe ingestion.")
elif glove_ingest.lower() == "y":
    print("Downloading and ingesting word vectors...")
    NewSearchTermExplorer(
        sample_terms=search_terms,
        vector_url="https://nlp.stanford.edu/data/wordvecs/glove.2024.wikigiga.50d.zip",
        unzip_path="./data/glove/",
    ).explore()

# collect some subreddit candidates
out_subs_csv = "data/sub_candidates.csv"
cols = [
    "sub_id",
    "sub_name",
    "sub_desc",
    "topic_group",
    "activity_level",
]
topic_labels = [
    "nutrition",
    "fitness",
    "gut",
    "digestion",
    "other",
]

# run CandidateReviewer on list of search terms
for term in tqdm(search_terms):
    print(f"Reviewing candidates for search term: {term}")
    reviewer = CandidateReviewer(
        reddit=reddit,
        search_term=term,
        sub_name=False,
        fieldnames=cols,
        topic_labels=topic_labels,
        sub_limit=25,
        model_name="facebook/bart-large-mnli",
        post_limit=100,
        active_post_days=50,
        recent_post_days=7,
        avg_comment_cnt_limit=3,
        unique_poster_cnt_limit=30,
        num_subscribers_limit=1000,
        writer_batch_size=500,
    )
    reviewer.execute()
