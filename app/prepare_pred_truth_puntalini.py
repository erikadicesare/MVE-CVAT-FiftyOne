import random
import pandas as pd
import os, shutil

data=pd.read_excel(io='/home/musausr/Downloads/Puntalini.xlsx')

#print(data)
columns = ['ObjKey', 'idSample', 'Lunghezza (mm)', 'Larghezza (mm)', 'Integrità (%)', 'Inclinazione (°)']

names = []
for filename in os.listdir('/home/musausr/puntalini/Puntalini'):
    #print(filename)
    names.append(filename.split('_')[0])

identificatore = 13

rows = []
for index, row in data.iterrows():
    sampleName='202212011416{}30'.format(identificatore)
    lung = row[columns[2]]
    larg = row[columns[3]]
    integ = row[columns[4]]
    incl = row[columns[5]]
    for name in names:
        currentRow = []
        if sampleName in name:
            currentRow.append(str(name))
            currentRow.append(index+1)
            currentRow.append('%.1f'%(lung + random.uniform(-1, 1)))
            currentRow.append('%.1f'%(larg + random.uniform(-1, 1)))
            currentRow.append(integ + random.randint(-5, 5))
            currentRow.append(incl + random.randint(-2, 2))
            rows.append(currentRow)
    identificatore = identificatore + 1

    print(rows)

df = pd.DataFrame(data=rows, columns=columns)
namefile = "/home/musausr/Downloads/puntalini.xlsx"
df.to_excel(namefile, index=False, header=True)