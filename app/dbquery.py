from pathlib import Path
import mysql.connector
from app import CVATapi
import ntpath, os
from dotenv import load_dotenv

load_dotenv()

user_db = os.getenv('USER_DB')
name_db = os.getenv('NAME_DB')
#pw_db = os.getenv('PW_DB')

params = {
    'user': user_db, 
    'database': name_db,
    #'password': pw_db
}

# creazione nuovo progetto MVE 
def new_projectMVE(name_prj, desc_prj, img_prj):

    mydb = mysql.connector.connect(**params)

    # salvo l'immagine inserita dall'utente nella cartella /static/data/project-icon/ 
    headfp, tailfp = ntpath.split(img_prj.filename)
    url_img_prj = './app/static/data/project-icon/' + tailfp
    img_prj.save(url_img_prj)
    relative_path = "data/project-icon/" + tailfp

    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectsMVE (NomeProgetto, Descrizione, ImmagineDescrittiva) VALUES (%s, %s, %s)"
    val = (name_prj, desc_prj, relative_path)
    mycursor.execute(sql, val)

    mydb.commit()

    mycursor.close()

    mydb.close()

# modifica di un progetto MVE
def edit_projectMVE(id_prj, name_prj, desc_prj, img_prj):

    mydb = mysql.connector.connect(**params)

    # se l'utente decide di non modificare l'immagine, vado aprendere quella esistente, altrimenti uso quella appena inserita
    if img_prj.filename == '':
        mycursor = mydb.cursor()
        mycursor.execute("SELECT ImmagineDescrittiva FROM ProjectsMVE WHERE IdProjectMVE=%s", (id_prj,))
        projectsMVE = mycursor.fetchone()
        relative_path = projectsMVE[0]
    else:
        headfp, tailfp = ntpath.split(img_prj.filename)
        url_img_prj = './app/static/data/project-icon/' + tailfp
        img_prj.save(url_img_prj)
        relative_path = "data/project-icon/" + tailfp

    mycursor = mydb.cursor()

    mycursor.execute ("""
    UPDATE ProjectsMVE
    SET NomeProgetto=%s, Descrizione=%s, ImmagineDescrittiva=%s
    WHERE IdProjectMVE=%s
    """, (name_prj, desc_prj, relative_path, id_prj))

    mydb.commit()

    mycursor.close()
    mydb.close()

# eliminazione di un progetto MVE (in automatico elimina i progetti CVAT associati perché c'è l'opzione on cascade nel db)
def delete_projectMVE(id_prj):

    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM ProjectsMVE WHERE IdProjectMVE=%s", (id_prj,))

    mydb.commit()
    
    mycursor.close()
    mydb.close()

# eliminazione di un progetto CVAT 
def delete_projectCVAT(id_prj):

    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM ProjectMVExProjectCVAT WHERE IdProjectCVAT=%s", (id_prj,))

    mydb.commit()

    mycursor.close()
    mydb.close()

# creazione di un nuovo progetto CVAT nel db (coppia di chiavi idMVExidCVAT)
def new_projectCVAT(id_prj_MVE, id_prj_CVAT):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO ProjectMVExProjectCVAT (IdProjectMVE, IdProjectCVAT) VALUES (%s, %s)"
    val = (id_prj_MVE, id_prj_CVAT)
    mycursor.execute(sql, val)

    mydb.commit()

    mycursor.close()
    mydb.close()

# ottengo tutti i progetti MVE
def get_projectsMVE():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE")
    projectsMVE = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return projectsMVE

# ottengo un progetto mve specifico
def get_projectMVE(id):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectsMVE WHERE IdProjectMVE=%s", (id,))
    projectsMVE = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    if (projectsMVE==[]):
        return projectsMVE
    else:
        return projectsMVE[0]


# ottengo tutti i progetti CVAT associati a un progetto MVE specifico
def get_projectsCVAT(id):

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectMVExProjectCVAT WHERE IdProjectMVE=%s", (id,))
    projectsCVAT = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return projectsCVAT

# ottengo un progetto CVAT specifico 
def get_projectCVAT(id):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectMVExProjectCVAT WHERE IdProjectCVAT=%s", (id,))
    projectCVAT = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    if (projectCVAT==[]):
        return projectCVAT
    else:
        return projectCVAT[0]

# creo array di oggetti, un oggetto per ogni progetto CVAT.
# per ogni progetto CVAT faccio una chiamata alla funzione get_project che mi restituisce le informazioni 
# un oggetto con le informazioni del progetto CVAT (nome, numero di task, numero di immagini)
def get_projectMVExProjectCVAT():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM ProjectMVExProjectCVAT ")
    projectsCVAT = mycursor.fetchall()

    mycursor.close()
    mydb.close()
    
    psCVAT = []
    for projectCVAT in projectsCVAT:
        id_prj_MVE = projectCVAT[0]
        id_prj_CVAT = projectCVAT[1]
        project = CVATapi.get_project(id_prj_MVE, id_prj_CVAT)

        psCVAT.append(project)

    return psCVAT

# prendo gli id dei progetti cvat presenti del db
def get_projectsCVAT_id():

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT IdProjectCVAT FROM ProjectMVExProjectCVAT ")
    projectsCVAT = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    ids = []
    if (len(projectsCVAT) != 0):

        for pCVAT in projectsCVAT:
            ids.append(pCVAT[0])

    return ids

# creo una istanza nella tabella Truth
def insert_truth(idMVE, name):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO Truth (IdProjectMVE, Name) VALUES (%s, %s)"
    val = (idMVE, name)
    mycursor.execute(sql, val)

    mydb.commit()
    ItemID = mycursor.lastrowid

    mycursor.close()
    mydb.close()

    return ItemID

# creo una istanza nella tabella TruthValues
def insert_truth_values(idTruth, propName, valReal, valStr):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    sql = "INSERT INTO TruthValues (IdTruth, PropName, ValueReal, ValueString) VALUES (%s, %s, %s, %s)"
    val = (idTruth, propName, valReal, valStr)
    mycursor.execute(sql, val)

    mydb.commit()

    mycursor.close()
    mydb.close()


# prendo i valori corrispondenti ad un certo idSample dalla tabella TruthValues
def get_truth_values(idSample):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM TruthValues WHERE IdTruth=%s", (idSample,))

    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return results

# prendo le proprieta corrispondenti ad un certo idSample dalla tabella TruthValues
def get_truth_prop_names(idSample):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("SELECT PropName FROM TruthValues WHERE IdTruth=%s", (idSample,))

    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return results

# elimino le righe con le proprieta corrispondenti ad un determinato idSample
def delete_truth_value(idSample):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM TruthValues WHERE idTruth=%s", (idSample,))

    mydb.commit()

    mycursor.close()
    mydb.close()

# ottento le righe dalla tabella Truth con un determinato IdProjectMVE
def get_truth_mve(idMVE):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM Truth WHERE IdProjectMVE=%s", (idMVE,))
    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return results

# ottento i samples Id dalla tabella Truth
def get_sampleIds_truth():
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT IdSample FROM Truth")
    sampleIds = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    ids = []
    if (len(sampleIds) != 0):

        for sId in sampleIds:
            ids.append(sId[0])

    return ids

# ottento i samples name dalla tabella Truth
def get_sampleNames_truth():
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT Name FROM Truth")
    sampleNames = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    names = []
    if (len(sampleNames) != 0):

        for sName in sampleNames:
            names.append(sName[0])

    return names

# ottento i samples name e id dalla tabella Truth di uno specifico progetto mve
def get_sampleIdNames_truth_MVE(idMVE):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT IdSample, Name FROM Truth WHERE IdProjectMVE=%s", (idMVE,))
    samples = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    samplesIdName = []
    if (len(samples) != 0):

        for sample in samples:
            samplesIdName.append({
                'id': sample[0],
                'name': sample[1]
            })

    return samplesIdName

# ottento i samples name dalla tabella Truth
def get_id_from_name_truth(name):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT IdSample FROM Truth WHERE Name=%s", (name,))
    id = mycursor.fetchone()

    mycursor.close()
    mydb.close()

    if (id==[]):
        return id
    else:
        return id[0]

# cancello la riga in Truth corrispondente ad un dato nome
def delete_truth(name):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM Truth WHERE Name=%s", (name,))
    
    mydb.commit()

    mycursor.close()
    mydb.close()

    #return myresult

# mi segno le tabelle che hanno nel nome la stirnga "Prediction" (per fare il count in predictdb)
def count_table():
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("Show tables;")
 
    myresult = mycursor.fetchall()
    
    predTables = []
    for x in myresult:
        if 'Prediction' in x[0]:
            predTables.append(x[0])
    
    return len(predTables)


# controllo che se la tabella passata come parametro esiste
def check_table_exists(name_table):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{}'
        """.format(name_table))
    if mycursor.fetchone()[0] == 1:
        mydb.close()
        return True
        
    mydb.close()
    return False

# creo una tabella Prediction 
def create_table_prediction(name_table):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = "CREATE TABLE {} (idMVS VARCHAR(100) PRIMARY KEY)".format(name_table) 
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

# aggiungo una colonna a una specifica tabella Prediction
def add_column_prediction(name_table, name_column, type_column):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    sql = "ALTER TABLE {} ADD `{}` {}".format(name_table, name_column, type_column)
    mycursor.execute(sql)

    mycursor.close()
    mydb.close()

# aggiungo la tabella con chiave esterna (idSample) a una specifica tabella Prediction 
def add_column_prediction_fk(name_table):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    sql_col = "ALTER TABLE {} ADD IdSample BIGINT NOT NULL".format(name_table)

    mycursor.execute(sql_col)

    sql_fk = "ALTER TABLE {} ADD CONSTRAINT {}_FK FOREIGN KEY (IdSample) REFERENCES Truth(IdSample) ON DELETE CASCADE ON UPDATE CASCADE".format(name_table, name_table)

    mycursor.execute(sql_fk)

    mycursor.close()
    mydb.close()

# inserisco una riga ad una tabella specifica Prediction 
def insert_prediction_row(name_table, values):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    par = ""
    for val in values:
        par = par + "%s,"
    
    sql = "INSERT INTO {} VALUES ({})".format(name_table, par[:-1])

    val = tuple(i for i in values)
    
    mycursor.execute(sql, val)

    mydb.commit()
    mycursor.close()
    mydb.close()

# inserisco una riga alla tabella PredList
def insert_pred_list(idPred, name, idMVE):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = "INSERT INTO PredList (IdPrediction, Name, IdProjectMVE) VALUES (%s, %s, %s)"
    val = (idPred, name, idMVE)
    mycursor.execute(sql, val)

    mydb.commit()
    ItemID = mycursor.lastrowid

    mycursor.close()
    mydb.close()

    return ItemID

# Prendo le righe della tabella PredList che hanno un determinato progetto mve associato
def get_predList_by_id(idMVE):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM PredList WHERE IdProjectMVE=%s", (idMVE,))
    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    predictions = []

    for res in results:
        countRows = count_rows_table(res[1])
        pred = {
            'id': res[0],
            'IdPrediction': res[1],
            'Name': res[2],
            'IdProjectMVE': res[3],
            'rows': countRows
        }
        predictions.append(pred)
    #get_n_rows_for_prediction(2)

    return predictions

# Prendo le righe della tabella PredList
def get_predList(idMVE):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM PredList")
    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    predictions = []

    for res in results:
        countRows = count_rows_table(res[1])
        pred = {
            'id': res[0],
            'IdPrediction': res[1],
            'Name': res[2],
            'IdProjectMVE': res[3],
            'rows': countRows
        }
        predictions.append(pred)
    #get_n_rows_for_prediction(2)

    return predictions

# Prendo gli id della tabella PredList che hanno un determinato progetto mve associato
def get_predList_ids(idMVE):
    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()
    mycursor.execute("SELECT IdPrediction FROM PredList WHERE IdProjectMVE=%s", (idMVE,))
    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    predictions = []

    for pred in results:
        predictions.append(pred[0])

    return predictions

# eliminazione di una predizione
def delete_prediction(id):

    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM PredList WHERE id=%s", (id,))

    mydb.commit()

    mycursor.close()
    mydb.close()

# seleziona una tabella di predizioni e ne restituisce il numero di righe
def count_rows_table(table_name):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("Show tables;")
 
    myresult = mycursor.fetchall()
    mycursor.close()
    
    tables = []
    for table in myresult:
        tables.append(table[0])

    if table_name in tables:
        mycursor = mydb.cursor()
        sql = "SELECT COUNT(*) FROM {};".format(table_name)
        mycursor.execute(sql)
        count_row = mycursor.fetchone()
        mycursor.close()
        mydb.close()
        return count_row[0]
    
    mydb.close()
    return []

# creo una istanza nella tabella MVSxCVAT 
def insert_MVSxCVAT_row(idCVAT, idMVE, idTask):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    sql = "INSERT INTO MVSxCVAT (IdCVAT, IdProjectMVE, IdTask) VALUES (%s, %s, %s)"

    val = (idCVAT, idMVE, idTask)
    
    mycursor.execute(sql, val)

    mydb.commit()
    mycursor.close()
    mydb.close()

# prendo la colonna idMVS di una determinata tabella PredictionX
def get_prediction_ids(table_name):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = "SELECT idMVS FROM {};".format(table_name)
    mycursor.execute(sql)

    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    ids = []
    if (len(results) != 0):

        for id in results:
            ids.append(id[0])

    return ids

# seleziono le righe della tabella MVSxCVAT che hanno un determinato IdProjectMVE
def get_MVSxCVAT_byMVE(idMVE):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM MVSxCVAT WHERE IdProjectMVE=%s", (idMVE,))

    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return results


# seleziono le righe della tabella MVSxCVAT
def get_MVSxCVAT(idCVAT, idMVE):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("SELECT COUNT(*) FROM MVSxCVAT WHERE IdCVAT=%s AND IdProjectMVE=%s", (idCVAT, idMVE))
    count = mycursor.fetchone()
    mycursor.close()
    mydb.close()
    return count[0]

# cancello le righe della tabella MVSxCVAT che hanno un determinato idTask
def delete_MVSxCVAT_task(idTask):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM MVSxCVAT WHERE IdTask=%s", (idTask,))

    mydb.commit()

    mycursor.close()
    mydb.close()

# cancello le righe della tabella MVSxCVAT che hanno un determinato idMVE
def delete_MVSxCVAT_MVE(idMVE):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()
    
    mycursor.execute("DELETE FROM MVSxCVAT WHERE IdProjectMVE=%s", (idMVE,))

    mydb.commit()

    mycursor.close()
    mydb.close()

# prendo i nomi delle colonne di una tabella
def get_columns_name_table(name_table):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    # query to get the names of the columns
    mycursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (name_db, name_table))

    columns = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return columns

# prendo i tipi delle colonne di una tabella
def get_columns_type_table(name_table):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    # query to get the type of the columns
    mycursor.execute("SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (name_db, name_table))

    datatype = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return datatype

# prendo tutti campi di una tabella 
def get_prediction(table_name):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    sql = "SELECT * FROM {};".format(table_name)
    mycursor.execute(sql)

    results = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return results

# prendo i nomi delle colonne di una tabella
def get_prediction_columns(table_name):
    mydb = mysql.connector.connect(**params)
    mycursor = mydb.cursor()

    mycursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (name_db, table_name))
    columns = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    return columns

