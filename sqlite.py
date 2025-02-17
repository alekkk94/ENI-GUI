# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 14:44:30 2025

@author: alekd
"""

import sqlite3
import pandas as pd
import time
import os
db_folder=r'C:\Users\alekd\OneDrive - Politecnico di Milano\Projects\ENI - BESSence\GUI'
db_name = 'example.db'
TABLE_NAME = "measurements_5min"
data_folder = r'C:/Users/alekd/Politecnico di Milano/Matteo Spiller - BESSence/00_database_assemini/Assemini BESS_BAU_2023-08-01T0000_2024-12-01T0000_5min'

def create_sql(db_name,db_folder):
    connection=sqlite3.connect(os.path.join(db_folder,db_name))
    connection.commit()
    connection.close()
def create_table(db_folder,db_name,TABLE_NAME):
    connection=sqlite3.connect(os.path.join(db_folder,db_name))
    cursor = connection.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "Name" TEXT NOT NULL,
            "P_AC" REAL,
            "P_DC" REAL,
            "SoH" REAL,
            "V" REAL,
            "SoC" REAL,
            "Timestamp" DATETIME,
            CONSTRAINT unique_name_timestamp UNIQUE ("Name", "Timestamp")
        )
    """)

    connection.commit()
    connection.close()
def list_tables(db_folder,db_name):
    connection=sqlite3.connect(os.path.join(db_folder,db_name))
    cursor = connection.cursor()

    # Query to fetch all table names from sqlite_master
    query = "SELECT name FROM sqlite_master WHERE type='table';"

    # Execute the query and fetch all results
    cursor.execute(query)
    tables = cursor.fetchall()

    # Close the connection
    connection.close()

    # Return the list of table names
    return [table[0] for table in tables]
def populate_table(db_folder,db_name,TABLE_NAME,data_folder):
    connection=sqlite3.connect(os.path.join(db_folder,db_name))
    cursor = connection.cursor()
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder,filename)
        bess_data = pd.read_parquet(file_path,engine='pyarrow')
        name = filename.split('.')[0]

        bess_data.rename(columns={'power dc side|5min|avg|'+name: 'P_DC', 'power ac side|5min|avg|'+name: 'P_AC','state of health|5min|avg|'+name:'SoH'
                                  ,'voltage dc side|5min|avg|'+name:'V','state of charge|5min|avg|'+name:'SoC'}, inplace=True)
        bess_data.reset_index(inplace=True,drop=False)
        bess_data = bess_data[['Timestamp','P_DC','P_AC','SoH','V','SoC']]
        bess_data['Name'] = name
        bess_data.to_sql(TABLE_NAME,connection, if_exists='append', index=False)
        print(f"{name} inverter inserted in the database.")
        connection.commit()
    connection.close()
def fetch_data(db_folder,db_name,TABLE_NAME,start_date,end_date,name_value):
    connection=sqlite3.connect(os.path.join(db_folder,db_name))
    cursor = connection.cursor()
    query = f"""
    SELECT * 
    FROM {TABLE_NAME} 
    WHERE Timestamp BETWEEN '{start_date}' AND '{end_date}'
    AND Name = '{name_value}'
    """
    queried_data = pd.read_sql(query, connection)
    connection.close()
    return queried_data
def fetch_all_inverters(db_folder,db_name,TABLE_NAME,start_date,end_date):
    connection=sqlite3.connect(os.path.join(db_folder,db_name))
    cursor = connection.cursor()
    query = f"""
    SELECT * 
    FROM {TABLE_NAME} 
    WHERE Timestamp BETWEEN '{start_date}' AND '{end_date}'
    """
    queried_data = pd.read_sql(query, connection)
    connection.close()
    return queried_data
# #OPTION 1 for query
# st=time.time()
# cursor.execute(f"SELECT * FROM {TABLE_NAME}")
# rows = cursor.fetchall()
# end=time.time()
# for row in rows:
#     print(row)
def main():
    db_folder=r'C:\Users\alekd\OneDrive - Politecnico di Milano\Projects\ENI - BESSence\GUI'
    db_name = 'example.db'
    TABLE_NAME = "measurements_5min"
    data_folder = r'C:/Users/alekd/Politecnico di Milano/Matteo Spiller - BESSence/00_database_assemini/Assemini BESS_BAU_2023-08-01T0000_2024-12-01T0000_5min'
    
    create_sql(db_name,db_folder)
    
    create_table(db_folder,db_name,TABLE_NAME)
    
    list_tables(db_folder,db_name)
    
    st=time.time()
    populate_table(db_folder,db_name,TABLE_NAME,data_folder)
    end=time.time()
    
    start_date = '2024-01-01'
    end_date = '2024-01-31'
    
    # Define the Name value you want to filter by
    name_value = '2_2_1'
    bess_data = fetch_data(db_folder,db_name,TABLE_NAME,start_date,end_date,name_value)
    len(bess_data)