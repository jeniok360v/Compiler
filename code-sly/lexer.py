from sly import Lexer

class MyLexer(Lexer):
    tokens = { PROGRAM, PROCEDURE, IS, BEGIN, END, ASSIGN, IF, THEN, T, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, FOR, FROM, TO, DOWNTO, ENDFOR, WRITE, READ, NEQ, GEQ, LEQ, PIDENTIFIER, NUM }
    ignore = ' \t\r\n'
    literals = { '+', '-', '*', '/', '%', '=', '>', '<', '[', ']', '(', ')', ':', ',', ';' }

    # Token regex patterns
    PROGRAM = r'PROGRAM'
    PROCEDURE = r'PROCEDURE'
    IS = r'IS'
    BEGIN = r'BEGIN'
    ASSIGN = r':='
    ENDFOR = r'ENDFOR'
    ENDWHILE = r'ENDWHILE'
    ENDIF = r'ENDIF'
    DOWNTO = r'DOWNTO'
    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    END = r'END'
    WHILE = r'WHILE'
    DO = r'DO'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    FOR = r'FOR'
    FROM = r'FROM'
    WRITE = r'WRITE'
    READ = r'READ'
    NEQ = r'!='
    GEQ = r'>='
    LEQ = r'<='
    PIDENTIFIER = r'[_a-z]+'
    NUM = r'[0-9]+'
    TO = r'TO'
    T = r'T'

    @_(r'\#.*')
    def comment(self, t):
        pass

    def error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        self.index += 1

    @_(r'[_a-z]+')
    def PIDENTIFIER(self, t):
        t.value = str(t.value)
        return t
    
    @_(r'[0-9]+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python lexer.py <inputfile>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as file:
        data = file.read()

    lexer = MyLexer()
    for tok in lexer.tokenize(data):
        print(tok)

if __name__ == '__main__':
    main()