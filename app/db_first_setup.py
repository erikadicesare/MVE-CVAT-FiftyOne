import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

user_db = os.getenv('USER_DB')
name_db = os.getenv('NAME_DB')
pw_db = os.getenv('PW_DB')
"""
params = {
    'user': '', ##### insert the name of the user 
    'password': '', #### insert the password
}

mydb = mysql.connector.connect(**params)
mycursor = mydb.cursor()

mycursor.execute("CREATE DATABASE `MVE Database`")
"""
params = {
    'user': user_db, ##### insert the name of the user 
    'password': pw_db, #### insert the password
    'database': 'MVE Database'
}

def create_ProjectsMVE():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = "CREATE TABLE ProjectsMVE (IdProjectMVE BIGINT(20) NOT NULL AUTO_INCREMENT, Name VARCHAR(100), Description MEDIUMTEXT, Image varchar(100), PRIMARY KEY (IdProjectMVE));" 
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

def create_ProjectMVExProjectCVAT():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = """
            CREATE TABLE ProjectMVExProjectCVAT 
            (IdProjectMVE BIGINT(20) NOT NULL, 
            IdProjectCVAT BIGINT(20) NOT NULL, 
            PRIMARY KEY (IdProjectMVE, IdProjectCVAT), 
            FOREIGN KEY (IdProjectMVE) REFERENCES ProjectsMVE(IdProjectMVE) ON DELETE CASCADE ON UPDATE CASCADE);
        """

    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

def create_Truth():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = """
            CREATE TABLE Truth 
            (IdSample BIGINT(20) NOT NULL AUTO_INCREMENT, 
            IdProjectMVE BIGINT(20) NOT NULL,
            Name VARCHAR(100) NOT NULL, 
            PRIMARY KEY (IdSample), 
            FOREIGN KEY (IdProjectMVE) REFERENCES ProjectsMVE(IdProjectMVE) ON DELETE CASCADE ON UPDATE CASCADE);
        """
        
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

def create_TruthValues():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = """
            CREATE TABLE TruthValues 
            (Id BIGINT(20) NOT NULL AUTO_INCREMENT,
            PropName VARCHAR(100),
            ValueReal DOUBLE,
            ValueString VARCHAR(100),
            IdSample BIGINT(20) NOT NULL,
            PRIMARY KEY (Id), 
            FOREIGN KEY (IdSample) REFERENCES Truth(IdSample) ON DELETE CASCADE ON UPDATE CASCADE);
        """
        
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

def create_PredList():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = """
            CREATE TABLE PredList 
            (Id BIGINT(20) NOT NULL AUTO_INCREMENT,
            TablePred VARCHAR(100) NOT NULL,
            Name VARCHAR(100) NOT NULL,
            IdProjectMVE BIGINT(20) NOT NULL,
            PRIMARY KEY (Id), 
            FOREIGN KEY (IdProjectMVE) REFERENCES ProjectsMVE(IdProjectMVE) ON DELETE CASCADE ON UPDATE CASCADE);
        """
        
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

def create_MVSxCVAT():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = """
            CREATE TABLE MVSxCVAT 
            (IdCVAT VARCHAR(100) NOT NULL,
            IdProjectMVE BIGINT(20) NOT NULL,
            IdTask VARCHAR(100) NOT NULL,
            PRIMARY KEY (IdCVAT, IdProjectMVE), 
            FOREIGN KEY (IdProjectMVE) REFERENCES ProjectsMVE(IdProjectMVE) ON DELETE CASCADE ON UPDATE CASCADE);
        """
        
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()


create_ProjectsMVE()
create_ProjectMVExProjectCVAT()
create_Truth()
create_TruthValues()
create_PredList()
create_MVSxCVAT()