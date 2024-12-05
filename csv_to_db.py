import pandas as pd
import sqlite3

csv_file = 'ufc-master-cleaned.csv'
df = pd.read_csv(csv_file, encoding='ascii')

conn = sqlite3.connect('ufc_database.db')


df.to_sql('ufc_data', conn, if_exists='replace', index=False)

conn.close()

print('CSV file has been converted to SQLite database successfully.')