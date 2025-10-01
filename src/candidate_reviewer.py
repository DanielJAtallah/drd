import praw
from datetime import datetime as dt, timedelta as td

### NOTES
# 1) Call subreddits by search term
# 2) Determine if subs are active - DONE
# 3) Search active subreddits for related subreddits
# 4) Use transformer to classify active subreddits by topic
# 5) Use data writer class to save results
#
# This function will be called by the main driver script
# iteravely for each search term.


class CandidateReviewer:
    """Accept search terms and reddit instance and iterates over candidate subreddits."""

    def __init__(
        self,
        reddit: praw.reddit.Reddit,
        search_term: str,
        current_time: dt = dt.now(),
    ):
        self.reddit = reddit
        self.search_term = search_term
        self.current_time = current_time

    def sub_search(self, sub_limit=25):
        """Search for subreddits matching the search term."""
        sub_generator = self.reddit.subreddits.search(self.search_term, limit=sub_limit)
        return sub_generator

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
