#Libraries installation in venv
python3 -m venv venv\
source venv/bin/activate\
pip install sly\
pip install -U pytest

#Executing example:
python compiler.py <input_file> <output_file>

#Executing all testcases at once:
pytest tests.py\
pytest tests.py -m basic\
pytest tests.py -m advanced\
pytest tests.py -vv
