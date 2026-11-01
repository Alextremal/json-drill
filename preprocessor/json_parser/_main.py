from ._parser import produce_ast 
from ._ast_to_py import ast_to_py

def parse_json(json: str) -> object:
    ast = produce_ast(json)
    py_obj = ast_to_py(ast)
    return py_obj

