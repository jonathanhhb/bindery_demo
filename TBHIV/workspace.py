import tempfile
import os
import shutil

tmp_prefix_dir = "/var/tmp/" if os.name == "posix" else "C:/Windows/Temp/"
workdir = tempfile.mkdtemp( prefix=tmp_prefix_dir )

source = os.listdir(".")
for files in source:
    if files.endswith(".py") or files.endswith( ".csv" ) or files == "dtk_centos.id":
        shutil.copy(files, workdir)

os.mkdir( os.path.join( workdir, "ep4_dir" ) )
source = os.listdir("ep4_dir")
for filename in source:
    if filename.endswith(".py"):
        shutil.copy("ep4_dir/" + filename, workdir + "/ep4_dir/")
 
os.chdir( workdir )
