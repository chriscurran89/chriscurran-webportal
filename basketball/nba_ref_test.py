#!/usr/bin/env python

import json
import pandas as pd
from . import db_utils as u
from itertools import filterfalse
from datetime import date
from datetime import timedelta
from basketball_reference_web_scraper import client


# for testing remove from production
import sys


def calc_points(x):
    try:
        x['points'] = (x['made_field_goals']*2) + \
            x['made_free_throws'] + x['made_three_point_field_goals']
    except:
        pass
    return x


def combine_nbaref_csvs(x, y):
    combined = x.append(y)
    return combined


class nbaref_fs():

    metrics = ['outcome', 'seconds_played', 'made_field_goals', 'attempted_field_goals', 'made_three_point_field_goals', 'attempted_three_point_field_goals',
               'made_free_throws', 'attempted_free_throws', 'offensive_rebounds', 'defensive_rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personal_fouls']

    game_metrics = pd.DataFrame(
        columns=['slug', 'date', 'metric_name', 'value'])

    def __init__(self):

        u.create_db_tables()
        # if there print print("Total metrics: " + str(GameMetric.objects.count()))
        print("Load complete...")

    def complete_historical_data(self):

        # Method to seed feature store
        box_scores = None

        last_date = date.today() - timedelta(days=1)

        while box_scores is None:

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            box_scores = calc_points(pd.DataFrame(
                client.player_box_scores(day=d, month=m, year=y)))
            box_scores['date'] = last_date

        # Delete after running correctly (or add some progress bar thing)
        y_check = y

        while y > 1950:

            last_date = last_date - timedelta(days=1)

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            new = calc_points(pd.DataFrame(
                client.player_box_scores(day=d, month=m, year=y)))
            new['date'] = last_date

            box_scores = box_scores.append(new)

            if y_check != y:
                print(str(y_check) + ' complete.')
                box_scores.to_csv('basketball/box_scores_all_of_them.csv')

            y_check = y

        box_scores.to_csv('basketball/box_scores_all_of_them.csv')

        return box_scores

    def parse_csv_to_db(self, file_path):

        box_data = pd.read_csv(file_path)

        # fit data model
        for index, row in box_data.iterrows():
            for metric in self.metrics:
                if metric == 'outcome' and row[metric] == 'Outcome.WIN':
                    row[metric] = 1
                elif metric == 'outcome' and row[metric] == 'Outcome.LOSS':
                    row[metric] = 0
                self.game_metrics = self.game_metrics.append(
                    {'slug': row['slug'], 'date': row['date'], 'metric_name': metric, 'value': row[metric]}, ignore_index=True)
                print(self.game_metrics)
                sys.exit()

        return str(file_path) + " was successfully added to the DB."

    # def players(self, team=True, slug='', season=False):
        # arrange all data by player attributes

    # def players(self, team=True, slug='', season=False):
        # arrange all data by player attributes

    # def feature_aggs(self, team=True, slug='', season=False):
        # catch all aggregation method
