import sqlite3
import os
import pandas as pd
from pandas import DataFrame

def create_db_tables():

	if not os.path.isfile('basketball.db'):

		conn = sqlite3.connect('basketball.db')  # You can create a new database by changing the name within the quotes
		c = conn.cursor() # The database will be saved in the location where your 'py' file is saved

		# Create table - GAMEMETRICS
		c.execute('''CREATE TABLE GAMEMETRICS
		             ([slug] INTEGER PRIMARY KEY,[date] date, [metric_name] text, [value] real)''')
		          
		# Create table - PLAYERS
		#c.execute('''CREATE TABLE PLAYERS
		#             ([generated_id] INTEGER PRIMARY KEY,[Country_ID] integer, [Country_Name] text)''')
		        
		# Create table - TEAMS
		#c.execute('''CREATE TABLE TEAMS
		#             ([Client_Name] text, [Country_Name] text, [Date] date)''')
		                 
		conn.commit()

	# Note that the syntax to create new tables should only be used once in the code (unless you dropped the table/s at the end of the code). 
	# The [generated_id] column is used to set an auto-increment ID for each record
	# When creating a new table, you can add both the field names as well as the field formats (e.g., Text)
	
	return "Database architecture in place..."

def add_game_metric():
	conn = sqlite3.connect('TestDB.db')  
	c = conn.cursor()

	read_clients = pd.read_csv (r'C:\Users\Ron\Desktop\Client\Client_14-JAN-2019.csv')
	read_clients.to_sql('CLIENTS', conn, if_exists='append', index = False) # Insert the values from the csv file into the table 'CLIENTS' 

	read_country = pd.read_csv (r'C:\Users\Ron\Desktop\Client\Country_14-JAN-2019.csv')
	read_country.to_sql('COUNTRY', conn, if_exists='replace', index = False) # Replace the values from the csv file into the table 'COUNTRY'

	# When reading the csv:
	# - Place 'r' before the path string to read any special characters, such as '\'
	# - Don't forget to put the file name at the end of the path + '.csv'
	# - Before running the code, make sure that the column names in the CSV files match with the column names in the tables created and in the query below
	# - If needed make sure that all the columns are in a TEXT format

	c.execute('''
	INSERT INTO DAILY_STATUS (Client_Name,Country_Name,Date)
	SELECT DISTINCT clt.Client_Name, ctr.Country_Name, clt.Date
	FROM CLIENTS clt
	LEFT JOIN COUNTRY ctr ON clt.Country_ID = ctr.Country_ID
	          ''')

	c.execute('''
	SELECT DISTINCT *
	FROM DAILY_STATUS
	WHERE Date = (SELECT max(Date) FROM DAILY_STATUS)
	          ''')
	   
	#print(c.fetchall())

	df = DataFrame(c.fetchall(), columns=['Client_Name','Country_Name','Date'])
	print (df) # To display the results after an insert query, you'll need to add this type of syntax above: 'c.execute(''' SELECT * from latest table ''')

	df.to_sql('DAILY_STATUS', conn, if_exists='append', index = False) # Insert the values from the INSERT QUERY into the table 'DAILY_STATUS'

	# export_csv = df.to_csv (r'C:\Users\Ron\Desktop\Client\export_list.csv', index = None, header=True) # Uncomment this syntax if you wish to export the results to CSV. Make sure to adjust the path name
	# Don't forget to add '.csv' at the end of the path (as well as r at the beg to address special characters)
