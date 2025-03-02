# Linraries installation in venv
python3 -m venv venv
source venv/bin/activate
pip install sly
pip install -U pytest
python compiler.py <input_file> <output_file>


------------------------
Files (v 1.0):
ast_nodes.py
codegen.py
compiler.py
lexer.py
parser.py
readme.md