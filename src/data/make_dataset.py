# -*- coding: utf-8-sig -*-
import praw
from praw.models import MoreComments
import pandas as pd
from psaw import PushshiftAPI
import datetime
import pandas_datareader.data as web


class RdtData:

    def __init__(self, client_id, client_key, username, passwd):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_key,
            password=passwd,
            user_agent="thesis",
            username=username,
            check_for_async=False)

    def get_data(self, start_date, end_date, subreddit, spam_user=[], num_comments=2, limit=None, date_list=[]):
        api = PushshiftAPI(self.reddit)

        def data_crawl(date, reddit, subreddit, spam_user, num_comments, limit):
            start_epoch = int(date.timestamp())
            et = date + datetime.timedelta(days=1)
            end_epoch = int(et.timestamp())
            submissions_generator = api.search_submissions(after=start_epoch,
                                                           before=end_epoch,
                                                           subreddit=subreddit,
                                                           limit=limit)
            submissions = list(submissions_generator)
            submissions_dict = {"id": [],
                                "url": [],
                                "title": [],
                                "score": [],
                                "num_comments": [],
                                "created_utc": [],
                                "selftext": [],
                                "top_comments": []}

            spam_user = spam_user
            for submission_id in submissions:
                submission_praw = reddit.submission(id=submission_id)
                submissions_dict["id"].append(submission_praw.id)
                submissions_dict["url"].append(submission_praw.url)
                submissions_dict["title"].append(submission_praw.title)
                submissions_dict["score"].append(submission_praw.score)
                submissions_dict["num_comments"].append(submission_praw.num_comments)
                submissions_dict["created_utc"].append(submission_praw.created_utc)
                submissions_dict["selftext"].append(submission_praw.selftext)
                submission_praw.comment_sort = "top"
                submission_praw.comment_limit = num_comments
                top_comments = []
                for comment in submission_praw.comments:
                    if isinstance(comment, MoreComments):
                        continue
                    if comment.author not in spam_user:
                        top_comments.append(comment.body)
                submissions_dict["top_comments"].append(' . '.join(top_comments))
            df = pd.DataFrame(submissions_dict)
            return df

        def all_load(start_date, end_date, reddit, subreddit, spam_user, num_comments, limit):
            df_fin = pd.DataFrame()
            date = start_date
            while date < end_date:
                df = data_crawl(date, reddit, subreddit, spam_user, num_comments, limit)
                df_fin = pd.concat([df_fin, df], axis=0)
                print('Reddit data for ' +
                      date.strftime("%y-%m-%d") +
                      ' collected. (' +
                      '{:.0%}'.format((date - start_date) / (end_date - start_date)) +
                      ')')
                date = date + datetime.timedelta(days=1)
            return df_fin

        def list_load(reddit, subreddit, spam_user, num_comments, limit, date_list):
            df_fin = pd.DataFrame()
            for date in date_list:
                df = data_crawl(date, reddit, subreddit, spam_user, num_comments, limit)
                df_fin = pd.concat([df_fin, df], axis=0)
                print('Reddit data for ' +
                      date.strftime("%y-%m-%d") +
                      ' collected. (' +
                      '{:.0%}'.format(date_list.index(date) / len(date_list)) +
                      ')')
            return df_fin

        if date_list:
            df_fin = list_load(self.reddit, subreddit, spam_user, num_comments, limit, date_list)
        else:
            df_fin = all_load(start_date, end_date, self.reddit, subreddit, spam_user, num_comments, limit)

        return df_fin


class FinData:

    def __init__(self, name, source):
        self.name = name
        self.source = source

    def get_data(self, start_date, end_date):
        df = web.DataReader(self.name, self.source, start_date, end_date)
        return df


def main():
    import os

    base_dir = 'D:\\github\\master_thesis_2022\\data\\interim'
    username = 'niyangbai'
    with open('pw.txt', 'r') as f:
        pw = f.read()
    cid = 'w66eheluJKCHiSWF8oZmfw'
    key = 'OlKg7Wd019ARZe50pgzqDPEdvG5OnA'
    start_date = datetime.datetime(2022, 2, 1)
    end_date = datetime.datetime(2022, 4, 1)
    spam_user = ['VisualMod', 'AutoModerator']
    subreddit = 'wallstreetbets'

    gme = FinData('GME', 'stooq')
    df_gme = gme.get_data(start_date, end_date)
    df_gme.to_csv(os.path.join(base_dir, 'df_gme.csv'), index=True, encoding='utf-8-sig')

    sp500 = FinData('sp500', 'fred')
    df_sp500 = sp500.get_data(start_date, end_date)
    df_sp500.to_csv(os.path.join(base_dir, 'df_sp500.csv'), index=True, encoding='utf-8-sig')

    trade_days = [i.to_pydatetime() for i in df_gme.index]

    api = RdtData(cid, key, username, pw)
    df_rdt = api.get_data(start_date, end_date, subreddit, spam_user, limit=5, date_list=trade_days)
    df_rdt.to_csv(os.path.join(base_dir, 'df_rdt.csv'), index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    main()
else:
    print('successfully imported')
