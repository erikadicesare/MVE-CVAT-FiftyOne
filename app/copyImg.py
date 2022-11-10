import shutil

source = '/home/musausr/images/cvat/Data_0_01_00_02_12.bmp'
for i in range(0,199):
    target = '/home/musausr/images/cvat/Data_0_01_00_02_12_{}.bmp'.format(i)
    shutil.copy(source, target)