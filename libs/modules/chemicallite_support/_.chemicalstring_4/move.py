
import os
import shutil

file_path = os.path.join(os.getcwd(), 'stringchemical.pyd')
dest_path = os.path.abspath(os.path.join(
	os.path.dirname(__file__), '..', 'stringchemical.pyd'))

shutil.copy(file_path, dest_path)

