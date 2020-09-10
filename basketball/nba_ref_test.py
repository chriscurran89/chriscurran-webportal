#!/usr/bin/env python

import json
import sqlite3
import pandas as pd
import numpy as np
from . import db_utils as u
from itertools import filterfalse
from datetime import date
from datetime import datetime
from datetime import timedelta
from basketball_reference_web_scraper import client


# for testing remove from production
import sys


def add_calc(x):

    try:
        x['points'] = (x['made_field_goals']*2) + x['made_free_throws'] + x['made_three_point_field_goals']
    except:
        pass

    try:
        x['total_rebounds'] = x['offensive_rebounds'] + x['defensive_rebounds']
    except:
        pass

    try:
        x['asst_to'] = round(x['assists'] / x['turnovers'], 1)
        x['asst_to'] = np.where(x['asst_to'] == np.inf, x['assists'], x['asst_to'])
        x['asst_to'] = x['asst_to'].fillna(0)
    except:
        pass

    try:
        x['minutes'] = round(x['seconds_played'] / 60, 2)
    except:
        pass

    return x


def combine_nbaref_csvs(x, y):
    combined = x.append(y)
    return combined


class nbaref_fs():

    metrics = ['outcome', 'seconds_played', 'made_field_goals', 'attempted_field_goals', 'made_three_point_field_goals', 'attempted_three_point_field_goals',
               'made_free_throws', 'attempted_free_throws', 'offensive_rebounds', 'defensive_rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personal_fouls',
               'points','total_rebounds','asst_to','minutes']

    game_metrics = pd.DataFrame(
        columns=['slug', 'date', 'metric_name', 'value'])

    def __init__(self):

        u.create_db_tables()
        try:
            print("Last download date: " + str(self.check_last_download()))
        except:
            print("No data...")

    def last_gameday(self):
        # Method to seed feature store
        box_scores = None

        last_date = date.today() - timedelta(days=1)

        while box_scores is None:

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            box_scores = add_calc(pd.DataFrame(
                client.player_box_scores(day=d, month=m, year=y)))
            box_scores['date'] = last_date

        return [box_scores, y, m, d]

    def complete_historical_data(self):

        last_gameday = self.last_gameday()
        box_scores = last_gameday[0]
        y = last_gameday[1]
        m = last_gameday[2]
        d = last_gameday[3]

        # Delete after running correctly (or add some progress bar thing)
        y_check = y

        while y > 1945:

            last_date = date(y,m,d) - timedelta(days=1)

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            new = add_calc(pd.DataFrame(
                client.player_box_scores(day=d, month=m, year=y)))
            new['date'] = last_date

            box_scores = box_scores.append(new)

            if y_check != y:
                print(str(y_check) + ' complete.')
                box_scores.to_csv('basketball/box_scores_all_of_them.csv')

            y_check = y

        box_scores.to_csv('basketball/box_scores_all_of_them.csv')

        return box_scores

    def last_gameday_to_date(self, y_in, m_in, d_in):

        last_gameday = self.last_gameday()
        box_scores = last_gameday[0]
        y = last_gameday[1]
        m = last_gameday[2]
        d = last_gameday[3]

        # Delete after running correctly (or add some progress bar thing)
        y_check = y

        while date(y,m,d) >= date(y_in,m_in,d_in):

            last_date = date(y,m,d) - timedelta(days=1)

            d = int(last_date.strftime('%d'))
            m = int(last_date.strftime('%m'))
            y = int(last_date.strftime('%Y'))

            new = add_calc(pd.DataFrame(
                client.player_box_scores(day=d, month=m, year=y)))
            new['date'] = last_date

            box_scores = box_scores.append(new)

            if y_check != y:
                print(str(y_check) + ' complete.')

            y_check = y

        box_scores.to_csv('basketball/box_scores_all_of_them.csv')


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
        
        conn = sqlite3.connect('basketball.db')

        self.game_metrics.to_sql('GAMEMETRICS', conn, if_exists='append', index = False) # Insert the values from the csv file into the table 'CLIENTS' 

        conn.commit()
        return "Metrics successfully added to database..."

    def pd_to_db(self, dataframe):

        # fit data model
        for index, row in dataframe.iterrows():
            for metric in self.metrics:
                if metric == 'outcome' and row[metric] == 'Outcome.WIN':
                    row[metric] = 1
                elif metric == 'outcome' and row[metric] == 'Outcome.LOSS':
                    row[metric] = 0
                self.game_metrics = self.game_metrics.append(
                    {'slug': row['slug'], 'date': row['date'], 'metric_name': metric, 'value': row[metric]}, ignore_index=True)
        
        conn = sqlite3.connect('basketball.db')
        
        try:
            self.game_metrics.to_sql('GAMEMETRICS', conn, if_exists='append', index = False)
            conn.commit()
            print("Metrics successfully added to database...")
        except:
            print("Nothing was added...")

    def check_last_download(self):
        conn = sqlite3.connect('basketball.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT date FROM GAMEMETRICS ORDER BY date DESC")
        last_date = datetime.strptime(c.fetchall()[0][0], '%Y-%m-%d')

        return last_date

    def update_db(self):

        try_date = self.check_last_download().date() + timedelta(days=1)

        d = int(try_date.strftime('%d'))
        m = int(try_date.strftime('%m'))
        y = int(try_date.strftime('%Y'))

        box_scores = self.last_gameday_to_date(y,m,d)

        self.pd_to_db(box_scores)

    def build_daily_tables(self):

        conn = sqlite3.connect('basketball.db')
        c = conn.cursor()
        c.execute('SELECT DISTINCT * FROM GAMEMETRICS')
        metric_table_dump = c.fetchall()
        metric_table = pd.DataFrame(metric_table_dump, columns=['slug','date','metric_name','value'])
        
        points = metric_table.loc[metric_table['metric_name'] == 'points'].sort_values(by='value', ascending=False)[0:9]
        points.to_csv('r/playoff_points.csv')

        total_rebounds = metric_table.loc[metric_table['metric_name'] == 'total_rebounds'].sort_values(by='value', ascending=False)[0:9]
        total_rebounds.to_csv('r/playoff_total_rebounds.csv')

        o_reb = metric_table.loc[metric_table['metric_name'] == 'offensive_rebounds'].sort_values(by='value', ascending=False)[0:9]
        o_reb.to_csv('r/playoff_o_reb.csv')

        asst_to = metric_table.loc[metric_table['metric_name'] == 'asst_to'].sort_values(by='value', ascending=False)[0:9]
        asst_to.to_csv('r/playoff_asst_to.csv')

        minutes = metric_table.loc[metric_table['metric_name'] == 'minutes'].sort_values(by='value', ascending=False)[0:9]
        minutes.to_csv('r/playoff_minutes.csv')

        return "Daily download saved to Rmarkdown doc location..."
        
