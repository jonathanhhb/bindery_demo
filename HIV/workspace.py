import tempfile
import os
import shutil
workdir = tempfile.mkdtemp( prefix="/var/tmp/" )
source = os.listdir(".")

for files in source:
    if files.endswith(".py") or files == "dtk_centos.id":
        shutil.copy(files, workdir)

os.chdir( workdir )
