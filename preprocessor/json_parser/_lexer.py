"""Create list of tokens (i.e. minimal significant units of json) so it would be easier for parser to proccess the input"""

import re
from enum import Enum
from dataclasses import dataclass

class TokenType(Enum):
    Whitespace = 0
    Lbrace = 1
    Rbrace = 2
    Lbracket = 3
    Rbracket = 4
    Colon = 5
    Comma = 6
    Boolean = 7
    String = 8
    Number = 9
    Null = 11
    EOF = 10

@dataclass
class TokenPos:
    row: int = 1
    col: int = 1

@dataclass
class Token:
    ttype: TokenType
    value: str
    pos: TokenPos

    def __repr__(self):
        return f"Token {{ value: \"{self.value}\"; type: {self.ttype}; pos: {self.pos} }}"

class Lexer:
    token_types = {
        TokenType.Whitespace: r'[ \n\t\r]',
        TokenType.Lbrace: '{',
        TokenType.Rbrace: '}',
        TokenType.Lbracket: r'\[',
        TokenType.Rbracket: r'\]',
        TokenType.Colon: ':',
        TokenType.Comma: ',',
        TokenType.Boolean: 'true|false',
        TokenType.String: '"[^"]*"',
        TokenType.Number: '[0-9]+',
        TokenType.Null: 'null',
    }

    def __init__(self, json: str):
        self.json = json
        self.raw_pos: int = 0
        self.token_list: list[Token] = []
        self.token_pos = TokenPos()

    def tokenize(self) -> list[Token]:
        while self._next_token(): pass
        self._exclude_whitespaces()
        self.token_list.append(self._create_eof_token())
        return self.token_list

    def _create_eof_token(self) -> Token:
        p = TokenPos(self.token_pos.row, self.token_pos.col+1)
        t = Token(TokenType.EOF, '\0', p)
        return t

    def _exclude_whitespaces(self):
        non_whitespace_tokens = [t for t in self.token_list if t.ttype != TokenType.Whitespace]
        self.token_list = non_whitespace_tokens

    """ Create next token and advance """
    def _next_token(self) -> bool:
        if self.raw_pos >= len(self.json):
            return False
        for token_type, regex in self.token_types.items():
            #_match = re.findall('^' + regex, self.json[self.raw_pos:])
            _match = re.match(regex, self.json[self.raw_pos:])
            if _match:
                match_str = _match.group()
                if match_str == '\n':
                    self.token_pos.row += 1
                    self.token_pos.col = 0

                curr_token_pos = TokenPos(self.token_pos.row, self.token_pos.col)
                token = Token(token_type, match_str, curr_token_pos)
                self.raw_pos += len(match_str)
                self.token_list.append(token)
                self.token_pos.col += len(match_str)
                return True

        print(f"Lexer: unknown pattern at {self.token_pos}")
        exit(1)

