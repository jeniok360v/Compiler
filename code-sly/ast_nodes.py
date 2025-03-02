class AstNode:
    def __init__(self):
        self.lineno = 0

    def print(self, indent=0):
        raise NotImplementedError

    def _print_indent(self, indent):
        print(' ' * indent, end='')


class ExpressionNode(AstNode):
    pass


class ValueNode(ExpressionNode):
    def __init__(self, value):
        self.value = value

    def print(self, indent=0):
        self._print_indent(indent)
        print(f"Value: {self.value}")


class IdentifierNode(ExpressionNode):
    def __init__(self, name, index=None, start=0, end=0, is_array_range=False, lineno=0):
        super().__init__()
        self.name = name
        self.index = index
        self.start = start
        self.end = end
        self.is_array_range = is_array_range
        self.lineno = lineno

    def print(self, indent=0):
        self._print_indent(indent)
        print(f"Identifier: {self.name}", end='')
        if self.is_array_range:
            print(f" [{self.start}:{self.end}]")
        elif self.index:
            print(" [", end='')
            self.index.print(0)
            print("]")
        else:
            print()

class BinaryExpressionNode(ExpressionNode):
    def __init__(self, left, right, operation):
        self.left = left
        self.right = right
        self.operation = operation

    def print(self, indent=0):
        self._print_indent(indent)
        print(f"Binary Expression: {self.operation}")
        self._print_indent(indent + 2)
        print("Left:")
        self.left.print(indent + 4)
        self._print_indent(indent + 2)
        print("Right:")
        self.right.print(indent + 4)


class ConditionNode(AstNode):
    def __init__(self, left_value, right_value, operation):
        self.left_value = left_value
        self.right_value = right_value
        self.operation = operation

    def print(self, indent=0):
        self._print_indent(indent)
        print("Condition:")
        self._print_indent(indent + 2)
        print("Left:")
        self.left_value.print(indent + 4)
        self._print_indent(indent + 2)
        print("Right:")
        self.right_value.print(indent + 4)
        self._print_indent(indent + 2)
        print(f"Operation: {self.operation}")


class DeclarationsNode(AstNode):
    def __init__(self):
        self.variables = []

    def add_variable_declaration(self, name):
        self.variables.append(IdentifierNode(name))

    def add_array_declaration(self, name, start, end):
        self.variables.append(IdentifierNode(name, start=start, end=end, is_array_range=True))

    def print(self, indent=0):
        self._print_indent(indent)
        print("Declarations:")
        for var in self.variables:
            var.print(indent + 2)


class CommandNode(AstNode):
    pass


class CommandsNode(AstNode):
    def __init__(self):
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    def size(self):
        return len(self.commands)

    def print(self, indent=0):
        self._print_indent(indent)
        print("Commands:")
        for cmd in self.commands:
            cmd.print(indent + 2)


class AssignNode(CommandNode):
    def __init__(self, identifier, expression, lineno=0):
        self.identifier = identifier
        self.expression = expression
        self.lineno = lineno

    def print(self, indent=0):
        self._print_indent(indent)
        print("AssignNode:")
        self._print_indent(indent + 2)
        print("Identifier:")
        self.identifier.print(indent + 4)
        self._print_indent(indent + 2)
        print("Expression:")
        self.expression.print(indent + 4)


class IfNode(CommandNode):
    def __init__(self, condition, then_commands, else_commands=None):
        self.condition = condition
        self.then_commands = then_commands
        self.else_commands = else_commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("IfNode:")
        self._print_indent(indent + 2)
        print("Condition:")
        self.condition.print(indent + 4)
        self._print_indent(indent + 2)
        print("Then:")
        self.then_commands.print(indent + 4)
        if self.else_commands:
            self._print_indent(indent + 2)
            print("Else:")
            self.else_commands.print(indent + 4)


class WhileNode(CommandNode):
    def __init__(self, condition, commands):
        self.condition = condition
        self.commands = commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("WhileNode:")
        self._print_indent(indent + 2)
        print("Condition:")
        self.condition.print(indent + 4)
        self._print_indent(indent + 2)
        print("Do:")
        self.commands.print(indent + 4)


class RepeatUntilNode(CommandNode):
    def __init__(self, condition, commands):
        self.condition = condition
        self.commands = commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("RepeatUntilNode:")
        self._print_indent(indent + 2)
        print("Condition:")
        self.condition.print(indent + 4)
        self._print_indent(indent + 2)
        print("Do:")
        self.commands.print(indent + 4)


class ForToNode(CommandNode):
    def __init__(self, pidentifier, from_value, to_value, commands):
        self.pidentifier = IdentifierNode(pidentifier)
        self.from_value = from_value
        self.to_value = to_value
        self.commands = commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("ForToNode:")
        self._print_indent(indent + 2)
        print("Variable:")
        self.pidentifier.print(indent + 4)
        self._print_indent(indent + 2)
        print("From:")
        self.from_value.print(indent + 4)
        self._print_indent(indent + 2)
        print("To:")
        self.to_value.print(indent + 4)
        self._print_indent(indent + 2)
        print("Do:")
        self.commands.print(indent + 4)


class ForDownToNode(CommandNode):
    def __init__(self, pidentifier, from_value, to_value, commands):
        self.pidentifier = IdentifierNode(pidentifier)
        self.from_value = from_value
        self.to_value = to_value
        self.commands = commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("ForDownToNode:")
        self._print_indent(indent + 2)
        print("Variable:")
        self.pidentifier.print(indent + 4)
        self._print_indent(indent + 2)
        print("From:")
        self.from_value.print(indent + 4)
        self._print_indent(indent + 2)
        print("Down To:")
        self.to_value.print(indent + 4)
        self._print_indent(indent + 2)
        print("Do:")
        self.commands.print(indent + 4)

class WriteNode(CommandNode):
    def __init__(self, value):
        self.value = value

    def print(self, indent=0):
        self._print_indent(indent)
        print("WriteNode:")
        self.value.print(indent + 2)


class ReadNode(CommandNode):
    def __init__(self, identifier):
        self.identifier = identifier

    def print(self, indent=0):
        self._print_indent(indent)
        print("ReadNode:")
        self.identifier.print(indent + 2)

class ProceduresNode(AstNode):
    def __init__(self):
        self.procedures = []

    def add_procedure(self, procedure):
        self.procedures.append(procedure)

    def print(self, indent=0):
        self._print_indent(indent)
        print("Procedures:")
        for procedure in self.procedures:
            procedure.print(indent + 2)

class ProcedureNode(AstNode):
    def __init__(self, procedure_head, declarations=None, commands=None):
        self.procedure_head = procedure_head
        self.declarations = declarations
        self.commands = commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("ProcedureNode:")
        self._print_indent(indent + 2)
        print("Procedure Head:")
        self.procedure_head.print(indent + 4)
        if self.declarations:
            self._print_indent(indent + 2)
            print("Declarations:")
            self.declarations.print(indent + 4)
        if self.commands:
            self._print_indent(indent + 2)
            print("Commands:")
            self.commands.print(indent + 4)

class ProcedureHeadNode(AstNode):
    def __init__(self, procedure_name, arguments_declaration):
        self.procedure_name = procedure_name
        self.arguments_declaration = arguments_declaration

    def print(self, indent=0):
        self._print_indent(indent)
        print(f"Procedure Head: {self.procedure_name}")
        if self.arguments_declaration:
            self._print_indent(indent + 2)
            print("Arguments Declaration:")
            self.arguments_declaration.print(indent + 4)


class ArgumentNode(AstNode):
    def __init__(self, argument_name, is_array=False):
        self.argument_name = argument_name
        self.is_array = is_array

    def print(self, indent=0):
        self._print_indent(indent)
        print(f"Argument: {self.argument_name}", end='')
        if self.is_array:
            print(" T")
        else:
            print()

class ArgumentsDeclarationNode(AstNode):
    def __init__(self):
        self.args = []

    def add_variable_argument(self, pidentifier):
        self.args.append(ArgumentNode(pidentifier))

    def add_array_argument(self, pidentifier):
        self.args.append(ArgumentNode(pidentifier, True))

    def print(self, indent=0):
        self._print_indent(indent)
        print("Arguments:")
        for arg in self.args:
            arg.print(indent + 2)

class ProcedureCallNode(CommandNode):
    def __init__(self, procedure_name, arguments):
        self.procedure_name = procedure_name
        self.arguments = arguments

    def print(self, indent=0):
        self._print_indent(indent)
        print(f"ProcedureCallNode: {self.procedure_name}")
        if self.arguments:
            self._print_indent(indent + 2)
            print("Arguments:")
            self.arguments.print(indent + 4)

class ProcedureCallArguments(AstNode):
    def __init__(self):
        self.arguments = []

    def add_argument(self, argument):
        self.arguments.append(argument)

    def print(self, indent=0):
        self._print_indent(indent)
        print("Procedure Call Arguments:")
        for arg in self.arguments:
            if arg:
                arg.print(indent + 2)



class MainNode(AstNode):
    def __init__(self, declarations, commands):
        self.declarations = declarations
        self.commands = commands

    def print(self, indent=0):
        self._print_indent(indent)
        print("Main:")
        if self.declarations:
            self.declarations.print(indent + 2)
        if self.commands:
            self.commands.print(indent + 2)


class ProgramNode(AstNode):
    def __init__(self, procedures=None, main=None):
        self.procedures = procedures
        self.main = main

    def print(self, indent=0):
        self._print_indent(indent)
        print("Program:")
        if self.procedures:
            self.procedures.print(indent + 2)
        if self.main:
            self.main.print(indent + 2)


