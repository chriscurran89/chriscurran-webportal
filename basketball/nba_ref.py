#!/usr/bin/env python

import json
import pandas as pd
from itertools import filterfalse
from datetime import date
from datetime import timedelta
from basketball_reference_web_scraper import client


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

    feature_store = []

    observation = {
        'slug': '',
        'date': '',
        'metric_name': '',
        'value': 0.
    }

    def __init__(self):

        try:
            with open('nba_ref/feature_store.txt') as f:
                self.feature_store = json.load(f)
                for o in self.feature_store:
                    print('slug: ' + o['slug'])
                    print('date: ' + o['date'])
                    print('metric_name: ' + o['metric_name'])
                    print('value: ' + str(o['value']))
                    print('\n- - -\n')
        except:
            with open('nba_ref/feature_store.txt', 'w') as f:
                json.dump(self.feature_store, f)

    def add_game_metrics(self, game_metrics):

        # Add method - needs to accept single and multiple game metrics
        with open('nba_ref/feature_store.txt') as f:
            self.feature_store = json.load(f)

        self.feature_store.append(game_metrics)

        with open('nba_ref/feature_store.txt', 'w') as f:
            json.dump(self.feature_store, f)

    def complete_historical_data(self, save=True):

        # Method to seed feature store
        box_scores = None

        last_date = date.today() - timedelta(days=1)

        while box_scores is None:

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            try:
                box_scores = calc_points(pd.DataFrame(
                    client.player_box_scores(day=d, month=m, year=y)))
                box_scores['date'] = last_date
            except:
                print('No games played on ' + str(last_date))
                last_date = last_date - timedelta(days=1)

        # Delete after running correctly (or add some progress bar thing)
        y_check = y
        while y > 1950:

            last_date = last_date - timedelta(days=1)

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            box_scores = box_scores.append(calc_points(
                pd.DataFrame(client.player_box_scores(day=d, month=m, year=y))))
            box_scores['date'] = last_date

            if y_check != y:
                print(str(y_check) + ' complete.')

                if save:
                    box_scores.to_csv('nba_ref/box_scores_all_of_them.csv')

            y_check = y

        if save:
            box_scores.to_csv('nba_ref/box_scores_all_of_them.csv')

        return box_scores

    def parse_csv_to_dict(self, file_path):

        # Parse nba reference downloads into feature store
        tmp_feature_storage = []

        box_data = pd.read_csv(file_path)

        # fit data model
        for index, row in box_data.iterrows():
            for metric in self.metrics:
                game_metric = {
                    'slug': row['slug'],
                    'date': row['date'],
                    'metric_name': metric,
                    'value': row[metric]
                }
                tmp_feature_storage.append(observation)

        return tmp_feature_storage

    def update_feature_store(self):

        # Find most recent box score date in feature store, update with recent data
        with open('nba_ref/feature_store.txt') as f:
            self.feature_store = json.load(f)

        self.feature_store.sort(key=lambda x: x['date'])

        return self.feature_store[:0]['date']

    # def players(self, team=True, slug='', season=False):
        # arrange all data by player attributes

    # def players(self, team=True, slug='', season=False):
        # arrange all data by player attributes

    # def feature_aggs(self, team=True, slug='', season=False):
        # catch all aggregation method
