"""Generate Python objects from AST"""

from ._ast import *
from ._parser import produce_ast

def _to_bool(value: str) -> bool:
    return True if value == 'true' else False

def gen_literal(value: Literal) -> str | int | bool | None:
    match value.literal_type:
        case LiteralType.Str:
            return value.value.strip('"')
        case LiteralType.Num:
            return int(value.value)
        case LiteralType.Bool:
            return _to_bool(value.value)
        case LiteralType.Null:
            return None

def gen_list(ast_list: List) -> list:
    assert isinstance(ast_list, List), f"{ast_list} is not of type List"
    py_list = list()
    for idx, expr in enumerate(ast_list.content):
        if isinstance(expr, Object):
            py_list.append(gen_obj(expr, name=f"List{idx+1}Object"))
        elif isinstance(expr, Literal):
            py_list.append(gen_literal(expr))
        elif isinstance(expr, List):
            py_list.append(gen_list(expr))
        else:
            assert False, "Unknown expression type"
    return py_list

def gen_obj(ast_obj: Object, name='RootObject') -> object:
    assert isinstance(ast_obj, Object), f"{ast_obj} is not of type Object"
    attrs = {attr.label: attr.value for attr in ast_obj.body}
    py_attrs = dict()
    for label, value in attrs.items():
        if isinstance(value, Object):
            py_attrs[label.strip('"')] = gen_obj(value)
        elif isinstance(value, Literal):
            py_attrs[label.strip('"')] = gen_literal(value)
        elif isinstance(value, List):
            py_attrs[label.strip('"')] = gen_list(value)
        else:
            assert False, "Unknown expression type"

    fstring = '{{' + ', '.join([f"{attr}: {{self.{attr}}}" for attr in py_attrs]) + '}}'
    py_attrs['__str__'] = lambda self: fstring.format(self=self)

    RootObjectType = type(name, (object,), py_attrs)
    root_object = RootObjectType()
    return root_object

# TODO: No clue how to specify that object of new type is to be returned
def ast_to_py(ast: Expr) -> list | object:
    if isinstance(ast, Object):
        return gen_obj(ast)
    elif isinstance(ast, List):
        return gen_list(ast)
    elif isinstance(ast, Literal):
        return gen_literal(ast)
    else:
        assert False, "Unknown expression type"

