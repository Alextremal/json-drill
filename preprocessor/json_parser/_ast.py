"""Define nodes of the syntax tree and relations between them"""

from enum import Enum

class NodeType(Enum):
    Object = 0
    Literal = 1
    List = 2
    Attribute = 3

class LiteralType(Enum):
    Num = 0
    Str = 1
    Bool = 2
    Null = 3

class Stmt:
    def __init__(self, kind: NodeType):
        self.kind = kind

class Expr(Stmt):
    pass

class Literal(Expr):
    def __init__(self, literal_type: LiteralType, value: str):
        super().__init__(NodeType.Literal)
        self.literal_type = literal_type
        self.value = value

    def __repr__(self):
        return f"Literal {{ value: {self.value}, type: {self.literal_type} }}"

class Attribute(Stmt):
    def __init__(self, value: Expr, label: str):
        super().__init__(NodeType.Attribute)
        self.value = value
        self.label = label

    def __repr__(self):
        return f"Attribute {{ label: {self.label}, value: {self.value} }}"

class Object(Expr):
    def __init__(self, body: list[Attribute]):
        super().__init__(NodeType.Object)
        self.body = body

    def __repr__(self):
        return f"Object {{ body: {self.body} }}"

class List(Expr):
    def __init__(self, content: list[Expr]):
        super().__init__(NodeType.List)
        self.content = content

    def __repr__(self):
        return f"List {{ content: {self.content} }}"

