from sly import Parser
from lexer import MyLexer
from ast_nodes import *

class MyParser(Parser):
    tokens = MyLexer.tokens

    def __init__(self):
        super().__init__()
        self.lineno = 1
        self.error_line = None

    def error(self, token):
        if token:
            self.error_line = token.lineno
            raise Exception(f"Syntax error at line {token.lineno}, token: {token.value}")
        else:
            raise Exception("Syntax error at EOF")

    @_('procedures main')
    def program_all(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        program_node = ProgramNode(p[0], p[1])
        # raise ValueError(f"Undefined variable '{p[0]}' at line {p.lineno}")
        return program_node    

    @_('procedures procedure')
    def procedures(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.procedures.add_procedure(p.procedure)
        return p.procedures

    @_('procedure')
    def procedures(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        procedures_node = ProceduresNode()
        procedures_node.add_procedure(p.procedure)
        return procedures_node

    @_('procedure')
    def procedure(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return p.procedure

    @_('PROCEDURE proc_head IS declarations BEGIN commands END')
    def procedure(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ProcedureNode(p[1], p[3], p[5])
    # @_('PROCEDURE proc_head IS declarations BEGIN commands END')
    # def procedure(self, p):
    #     procedures_node = ProceduresNode()
    #     procedures_node.add_procedure(ProcedureNode(p[1], p[3], p[5]))
    #     return procedures_node

    @_('PROCEDURE proc_head IS BEGIN commands END')
    def procedure(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ProcedureNode(p[1], None, p[4])
    # @_('PROCEDURE proc_head IS BEGIN commands END')
    # def procedure(self, p):
    #     procedures_node = ProceduresNode()
    #     procedures_node.add_procedure(ProcedureNode(p[1], None, p[4]))
    #     return procedures_node

    @_('')
    def procedures(self, p):
        pass

    @_('PROGRAM IS declarations BEGIN commands END')
    def main(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return MainNode(p[2], p[4])

    @_('PROGRAM IS BEGIN commands END')
    def main(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return MainNode(None, p[3])

    @_('commands command')
    def commands(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.commands.add_command(p.command)
        return p.commands

    @_('command')
    def commands(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        commands_node = CommandsNode()
        commands_node.add_command(p.command)
        return commands_node

    @_('command')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return CommandNode()

    @_('identifier ASSIGN expression ";"')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return AssignNode(p[0], p[2])

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return IfNode(p[1], p[3], p[5])

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return IfNode(p[1], p[3], None)

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return WhileNode(p[1], p[3])

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return RepeatUntilNode(p[3], p[1])

    @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
    def command(self, p):
        node = ForToNode(p[1], p[3], p[5], p[7])
        self.error_line = getattr(p, 'lineno', 0)
        return node

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        node = ForDownToNode(p[1], p[3], p[5], p[7])
        self.error_line = getattr(p, 'lineno', 0)
        return node

    @_('proc_call ";"')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return p[0]

    @_('READ identifier ";"')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ReadNode(p[1])

    @_('WRITE value ";"')
    def command(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return WriteNode(p[1])

    @_('PIDENTIFIER "(" args_decl ")"')
    def proc_head(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ProcedureHeadNode(p[0], p[2])

    @_('PIDENTIFIER "(" args ")"')
    def proc_call(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ProcedureCallNode(p[0], p[2])

    @_('declarations "," PIDENTIFIER')
    def declarations(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.declarations.add_variable_declaration(p[2])
        return p.declarations

    @_('declarations "," PIDENTIFIER "[" NUM ":" NUM "]"')
    def declarations(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.declarations.add_array_declaration(p[2], p[4], p[6])
        return p.declarations

    @_('PIDENTIFIER')
    def declarations(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        declarations_node = DeclarationsNode()
        declarations_node.add_variable_declaration(p[0])
        return declarations_node

    @_('PIDENTIFIER "[" NUM ":" NUM "]"')
    def declarations(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        declarations_node = DeclarationsNode()
        declarations_node.add_array_declaration(p[0], p[2], p[4])
        return declarations_node

    @_('args_decl "," PIDENTIFIER')
    def args_decl(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.args_decl.add_variable_argument(p[2])
        return p.args_decl

    @_('args_decl "," T PIDENTIFIER')
    def args_decl(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.args_decl.add_array_argument(p[3])
        return p.args_decl

    @_('PIDENTIFIER')
    def args_decl(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        args_decl_node = ArgumentsDeclarationNode()
        args_decl_node.add_variable_argument(p[0])
        return args_decl_node

    @_('T PIDENTIFIER')
    def args_decl(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        args_decl_node = ArgumentsDeclarationNode()
        args_decl_node.add_array_argument(p[1])
        return args_decl_node

    @_('args "," PIDENTIFIER')
    def args(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        p.args.add_argument(IdentifierNode(p[2]))
        return p.args

    @_('PIDENTIFIER')
    def args(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        args_node = ProcedureCallArguments()
        args_node.add_argument(IdentifierNode(p[0]))
        return args_node

    @_('value "+" value',
       'value "-" value',
       'value "*" value',
       'value "/" value',
       'value "%" value')
    def expression(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return BinaryExpressionNode(p[0], p[2], p[1])

    @_('value "=" value',
       'value NEQ value',
       'value ">" value',
       'value "<" value',
       'value GEQ value',
       'value LEQ value')
    def condition(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ConditionNode(p[0], p[2], p[1])

    @_('value')
    def expression(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return p[0]

    @_('NUM')
    def value(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return ValueNode(p[0])

    @_('identifier')
    def value(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return p[0]

    @_('PIDENTIFIER')
    def identifier(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return IdentifierNode(p[0])

    @_('PIDENTIFIER "[" PIDENTIFIER "]"')
    def identifier(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        return IdentifierNode(p[0], IdentifierNode(p[2]))

    @_('PIDENTIFIER "[" NUM "]"')
    def identifier(self, p):
        self.error_line = getattr(p, 'lineno', 0)
        node = IdentifierNode(p[0], ValueNode(p[2]), lineno=p.lineno)
        # if p[0] not in self.declarations:
        #     raise Exception(f"Undefined variable '{p[0]}' at line {p.lineno}")
        # if p[0] not in self.array_variables:
        #     raise Exception(f"Line {p.lineno}: Variable '{p.PIDENTIFIER}' is not an array")
        return node