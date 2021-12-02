import tempfile
import os
import shutil
workdir = tempfile.mkdtemp( prefix="/var/tmp/" )
source = os.listdir(".")

for files in source:
    if files.endswith(".py"):
        shutil.copy(files, workdir)

os.chdir( workdir )
