import sqlite3
import os
import pandas as pd
from pandas import DataFrame

def create_db_tables():

	if not os.path.isfile('basketball.db'):

		conn = sqlite3.connect('basketball.db')  # You can create a new database by changing the name within the quotes
		c = conn.cursor() # The database will be saved in the location where your 'py' file is saved

		# Create table - GAMEMETRICS
		c.execute(
		'''CREATE TABLE GAMEMETRICS(
			slug CHAR(20),
			date DATE,
			metric_name CHAR(30),
			value FLOAT)
		''')
              
		conn.commit()

	print("...")
