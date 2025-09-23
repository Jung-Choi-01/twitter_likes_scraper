import sys

class Progress:
    def __init__(self, current, total) -> None:
        self.current = current
        self.total = total
        pass

    def print_progress(self, current, waiting, retry_cnt, no_tweets_limit, time_elapsed) -> None:
        self.current = current
        progress = current / self.total
        bar_length = 40
        progress_bar = (
            "["
            + "=" * int(bar_length * progress)
            + "-" * (bar_length - int(bar_length * progress))
            + "]"
        )
        if no_tweets_limit:
            if waiting:
                sys.stdout.write(
                    "\rTweets scraped : {} - waiting to access older tweets {} min on 15 min               ".format(
                        current, retry_cnt
                    )
                )
            else:
                sys.stdout.write(
                    "\rTweets scraped : {} at {:.2} t/s ({}s elapsed)                                      ".format(
                        current, current/time_elapsed if time_elapsed != 0 else 0.0, int(time_elapsed)
                    )
                )
        else:
            if waiting:
                sys.stdout.write(
                    "\rProgress: [{:<40}] {:.2%} {} of {} - waiting to access older tweets {} min on 15 min".format(
                        progress_bar, progress, current, self.total, retry_cnt
                    )
                )
            else:
                sys.stdout.write(
                    "\rProgress: [{:<40}] {:.2%} {} of {} at {:.2} t/s ({}s elapsed)                       ".format(
                        progress_bar, progress, current, self.total, current/time_elapsed if time_elapsed != 0 else 0.0, int(time_elapsed)
                    )
                )
        sys.stdout.flush()
