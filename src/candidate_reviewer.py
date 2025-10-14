import praw
from datetime import datetime as dt, timedelta as td
from data_writer import ensure_csv_header, BufferedCSVWriter
from transformers import pipeline
from collections import Counter


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
        sub_limit: int = 25,
        model_name: str = "facebook/bart-large-mnli",
        post_limit: int = 100,
        active_post_days: int = 50,
        recent_post_days: int = 7,
        avg_comment_cnt_limit: int = 3,
        unique_poster_cnt_limit: int = 30,
        num_subscribers_limit: int = 1000,
        writer_batch_size: int = 500,
    ):
        self.reddit = reddit
        self.search_term = search_term
        self.current_time = current_time
        self.sub_name = sub_name
        self.candidate_path = candidate_path
        self.fieldnames = fieldnames
        self.topic_labels = topic_labels
        self.sub_limit = sub_limit
        # initialize current candidate list if not exists
        ensure_csv_header(self.candidate_path, self.fieldnames)
        # initialize transformer pipeline for topic classification
        self.model_name = model_name
        self.classifier = pipeline("zero-shot-classification", model=self.model_name)
        # parameters for activity check
        self.post_limit = post_limit
        self.active_post_days = active_post_days
        self.recent_post_days = recent_post_days
        self.avg_comment_cnt_limit = avg_comment_cnt_limit
        self.unique_poster_cnt_limit = unique_poster_cnt_limit
        self.num_subscribers_limit = num_subscribers_limit
        self.writer_batch_size = writer_batch_size

    def sub_search(self) -> list:
        """Search for subreddits matching the search term."""
        if self.sub_name:
            sub_list = [self.reddit.subreddit(self.search_term)]
        elif self.sub_name is False:
            sub_list = list(
                self.reddit.subreddits.search(self.search_term, limit=self.sub_limit)
            )
        return sub_list

    def is_active(self, subreddit) -> str:
        """Determine if a subreddit is active based on number of subscribers and posts."""
        # collect some measures to create heuristics
        subs = list(subreddit.new(limit=self.post_limit))
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
            if (most_recent_post_ts - first_post_ts <= td(days=self.active_post_days))
            else 0
        )
        # check that most recent post is within last 7 days
        recent_post_ind = (
            1
            if (
                self.current_time - most_recent_post_ts
                <= td(days=self.recent_post_days)
            )
            else 0
        )
        # check that there are approximately x comments per post
        comment_freq_ind = 1 if (avg_num_comments >= self.avg_comment_cnt_limit) else 0
        # check that there are some number of unique posters
        unique_poster_ind = (
            1 if (unique_poster_cnt >= self.unique_poster_cnt_limit) else 0
        )
        # check that there are some number of subscribers
        subscriber_ind = 1 if (num_subscribers >= self.num_subscribers_limit) else 0
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

    def execute(self):
        """Execute the search, review, and write to file."""
        writer = BufferedCSVWriter(
            self.candidate_path, self.fieldnames, batch_size=self.writer_batch_size
        )
        sub_list = self.sub_search()
        for sub in sub_list:
            sub_id = sub.id
            sub_name = sub.display_name
            sub_desc = sub.public_description
            topic_group = self.classify_topic(sub)
            activity_level = self.is_active(sub)
            writer.append(
                {
                    "sub_id": sub_id,
                    "sub_name": sub_name,
                    "sub_desc": sub_desc,
                    "topic_group": topic_group,
                    "activity_level": activity_level,
                }
            )
        writer.close()
