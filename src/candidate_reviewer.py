import praw
from datetime import datetime as dt, timedelta as td
from data_writer import ensure_csv_header
from transformers import pipeline
from collections import Counter

### NOTES
# 1) Call subreddits by search term - DONE
# 2) Determine if subs are active - DONE
# 3) Use transformer to classify active subreddits by topic - IN PROGRESS
# 4) Script that iterates over sub_search sub_list - TODO


class CandidateReviewer:
    """Accept search terms and reddit instance and iterates over candidate subreddits."""

    def __init__(
        self,
        reddit: praw.reddit.Reddit,
        search_term: str,
        current_time: dt = dt.now(),
        sub_name: bool = False,
        candidate_path: str = "data/sub_candidates.csv",
        fieldnames: list[str] = [
            "sub_id",
            "sub_name",
            "sub_desc",
            "topic_group",
            "activity_level",
        ],
        topic_labels: list[str] = [
            "general nutrition",
            "fitness",
            "gut health",
            "other",
        ],
        model_name: str = "facebook/bart-large-mnli",
    ):
        self.reddit = reddit
        self.search_term = search_term
        self.current_time = current_time
        self.sub_name = sub_name
        self.candidate_path = candidate_path
        self.fieldnames = fieldnames
        self.topic_labels = topic_labels
        # initialize current candidate list if not exists
        ensure_csv_header(self.candidate_path, self.fieldnames)
        # initialize transformer pipeline for topic classification
        self.model_name = model_name
        self.classifier = pipeline("zero-shot-classification", model=self.model_name)

    def sub_search(self, sub_limit=25):
        """Search for subreddits matching the search term."""
        if self.sub_name:
            sub_list = [self.reddit.subreddit(self.search_term)]
        elif self.sub_name is False:
            sub_list = list(
                self.reddit.subreddits.search(self.search_term, limit=sub_limit)
            )
        return sub_list

    def is_active(
        self,
        subreddit,
        post_limit=100,
        active_post_days=50,
        recent_post_days=7,
        avg_comment_cnt_limit=3,
        unique_poster_cnt_limit=30,
        num_subscribers_limit=1000,
    ) -> str:
        """Determine if a subreddit is active based on number of subscribers and posts."""
        # collect some measures to create heuristics
        subs = list(subreddit.new(limit=post_limit))
        most_recent_post_ts = dt.fromtimestamp(subs[0].created_utc)
        first_post_ts = dt.fromtimestamp(subs[-1].created_utc)
        avg_num_comments = sum([post.num_comments for post in subs]) / len(subs)
        unique_poster_cnt = len(
            set([post.author for post in subs if post.author is not None])
        )
        num_subscribers = subreddit.subscribers
        # check that we get about x posts in the last y days
        post_freq_ind = (
            1
            if (most_recent_post_ts - first_post_ts <= td(days=active_post_days))
            else 0
        )
        # check that most recent post is within last 7 days
        recent_post_ind = (
            1
            if (self.current_time - most_recent_post_ts <= td(days=recent_post_days))
            else 0
        )
        # check that there are approximately x comments per post
        comment_freq_ind = 1 if (avg_num_comments >= avg_comment_cnt_limit) else 0
        # check that there are some number of unique posters
        unique_poster_ind = 1 if (unique_poster_cnt >= unique_poster_cnt_limit) else 0
        # check that there are some number of subscribers
        subscriber_ind = 1 if (num_subscribers >= num_subscribers_limit) else 0
        heuristic_sum = (
            post_freq_ind
            + recent_post_ind
            + comment_freq_ind
            + unique_poster_ind
            + subscriber_ind
        )
        match heuristic_sum:
            case 5:
                return "active"
            case 4:
                return "likely active"
            case 3:
                return "potentially active"
            case _:
                return "inactive"

    def classify_topic(self, subreddit) -> str:
        """Classify subreddit topic using a zero-shot classifier."""
        top_posts = subreddit.top(time_filter="all")
        class_output = []
        for post in top_posts:
            try:
                result = self.classifier(post.selftext, self.topic_labels)
                result = result["labels"][0]
                class_output.append(result)
                if len(class_output) >= 10:
                    # see if there was a tie
                    counts = Counter(class_output)
                    if (
                        len(counts) > 1
                        and counts.most_common(2)[0][1] != counts.most_common(2)[1][1]
                    ):
                        return counts.most_common(1)[0][0]
                    elif len(counts) == 1:
                        return counts.most_common(1)[0][0]
            except ValueError:
                continue
