import fiftyone as fo
import mysql.connector
from mysql.connector import errorcode
import ntpath

def create_fo_dataset(id):
    # The directory containing the source images
    data_path = "../task45/images/"

    # The path to the COCO labels JSON file
    labels_path = "../task45/annotations.xml"

    export_dir = "/home/musausr/fiftyone/datasets_generated/" + id

    # Import the dataset
    dataset = fo.Dataset.from_dir(
        dataset_type=fo.types.CVATImageDataset, #CVATImageDataset
        label_field="prediction1",
        data_path=data_path,
        labels_path=labels_path,
        include_id=True,
        name=id
    )

    # Export the dataset
    dataset.export(
        export_dir=export_dir,
        dataset_type=fo.types.CVATImageDataset
    )

    #session = fo.launch_app(dataset)


def get_numeric_data(dataset, dbname, tablename, filepathfield):

    # set params to connect to db
    params = {
        'user': "root", 
        'database': dbname
    }

    mydb = mysql.connector.connect(**params)

    mycursor = mydb.cursor()

    # query to get the names of the columns
    mycursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (dbname, tablename))

    columns = mycursor.fetchall()

    # query to get the type of the columns
    mycursor.execute("SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (dbname, tablename))

    datatype = mycursor.fetchall()

    # loop to add the fields (equal to the name of the columns)
    i = 0
    excluded_field = []
    for x in columns:
        if (x[0] != filepathfield):
            if (datatype[i][0] == 'float'):
                dataset.add_sample_field(x[0], fo.FloatField)
            elif (datatype[i][0] == 'int'):
                dataset.add_sample_field(x[0], fo.IntField)
            elif (datatype[i][0] == 'varchar'):
                dataset.add_sample_field(x[0], fo.StringField)
            else:
                excluded_field.append(x[0])
        i = i + 1

    # query to select all the rows of the table with the data   
    sql = "SELECT * FROM " + tablename
    mycursor.execute(sql)

    myresult = mycursor.fetchall()

    mydb.close()

    # Add numeric values taken from the rows to the field just created 
    with fo.ProgressBar() as pb:
        for sample in pb(dataset):
            i = 0
            sampleFilePath = sample.filepath
            headfp, tailfp = ntpath.split(sampleFilePath)
            for x in myresult:
                if (tailfp == x[0]):
                    for z in columns:
                        if (z[0] != filepathfield) and (z[0] not in excluded_field):
                            sample[z[0]] = x[i]
                        i = i + 1
            sample.save() 
