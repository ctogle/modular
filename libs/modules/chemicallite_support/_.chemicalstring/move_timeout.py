
import os
import shutil

file_path = os.path.join(os.getcwd(), 'stringchemical_timeout.pyd')
dest_path = os.path.abspath(os.path.join(
	os.path.dirname(__file__), '..', 'stringchemical_timeout.pyd'))

shutil.copy(file_path, dest_path)

