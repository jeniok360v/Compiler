from ast_nodes import *

COMPILER_RESERVED = 8

POINTER_HANDLING_ADDR = COMPILER_RESERVED - 3
MINUS_ONE_CONSTANT_ADDR = COMPILER_RESERVED - 2
ZERO_CONSTANT_ADDR = COMPILER_RESERVED - 1
ONE_CONSTANT_ADDR = COMPILER_RESERVED

class CodeGenerator:
    def __init__(self):
        self.instructions = []
        self.memory_counter = COMPILER_RESERVED + 1
        self.labels = {}
        self.label_counter = 0

        self.variables = {}
        self.array_info = {}
        self.placeholders = {}
        self.foriterators = {}
        self.procedure_args = {}
        self.procedures = []
        self.location = ["main"]

    class Procedure:
        def __init__(self):
            self.name = None
            self.address = None
            self.jump_address = None
            self.foriterators = {}
            self.declarations = {}
            self.declarations_array_info = {}
            self.declaration_is_declared = set()
            self.arguments = {}
            self.argument_is_array = set()

    def new_label(self):
        self.label_counter += 1
        return f"$L{self.label_counter}%"

    def add_instruction(self, instr):
        self.instructions.append(instr)

    def add_placeholder(self, label):
        self.placeholders[label] = len(self.instructions)

    def add_label(self, label):
        self.labels[label] = len(self.instructions)

    def resolve_placeholders(self):
        for label, index in self.placeholders.items():
            line = self.labels[label]
            for i, instruction in enumerate(self.instructions):
                if label in instruction:
                    self.instructions[i] = instruction.replace(label, str(index - line))

    def generate(self, node):
        method_name = f"gen_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_generate)
        method(node)

    def generic_generate(self, node):
        raise NotImplementedError(f"No generate method for {type(node).__name__}")

    def gen_ProgramNode(self, node):
        main_label = self.new_label()
        self.add_instruction(f"SET 0")
        self.add_instruction(f"STORE {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SET 1")
        self.add_instruction(f"STORE {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"SET -1")
        self.add_instruction(f"STORE {MINUS_ONE_CONSTANT_ADDR}")
        self.add_label(main_label)
        self.add_instruction(f"JUMP {main_label}")
        
        if node.procedures:
            self.generate(node.procedures)
        self.add_placeholder(main_label)
        self.generate(node.main)

    def gen_MainNode(self, node):
        if node.declarations:
            self.generate(node.declarations)
        self.generate(node.commands)

    def gen_CommandsNode(self, node):
        for command in node.commands:
            self.generate(command)

    def gen_AssignNode(self, node):
        self.generate(node.expression)
        if node.identifier.name in self.foriterators:
            raise Exception(f"\"{node.identifier.name}\" can't be modified")
        if node.identifier.name in self.array_info:
            if not node.identifier.index:
                raise Exception(f"Array '{node.identifier.name}' must be accessed with an index")           
            if isinstance(node.identifier.index, ValueNode): 
                self.add_instruction(f"STORE {self.get_memory_location(node.identifier)}")
            elif isinstance(node.identifier.index, IdentifierNode):
                self.add_instruction(f"STORE 2")
                memory_location = self.get_memory_location(node.identifier)
                self.add_instruction(f"LOAD 2")
                self.add_instruction(f"STOREI {memory_location}")
        elif node.identifier.name in self.variables:
            if node.identifier.index:
                raise Exception(f"Variable '{node.identifier.name}' is not an array")
            self.add_instruction(f"STORE {self.get_memory_location(node.identifier)}")
        else: #procedures
            procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
            if not procedure_it:
                raise Exception(f"\"{node.identifier.name}\" Undeclared (0x0001)")
            if node.identifier.name in procedure_it.foriterators:
                raise Exception(f"\"{node.identifier.name}\" can't be modified")
            if node.identifier.name in procedure_it.arguments:
                if node.identifier.name in procedure_it.argument_is_array:
                    if not node.identifier.index:
                        raise Exception(f"Array '{node.identifier.name}' must be accessed with an index")
                    self.add_instruction(f"STORE 1")
                    memory_location = self.get_memory_location(node.identifier, procedure_it)
                    self.add_instruction(f"LOAD 1")
                    self.add_instruction(f"STOREI {memory_location}")
                else:
                    if node.identifier.index:
                        raise Exception(f"Variable '{node.identifier.name}' is not an array")
                    self.add_instruction(f"STOREI {self.get_memory_location(node.identifier, procedure_it)}")            
            elif node.identifier.name in procedure_it.declarations:
                if node.identifier.name in procedure_it.declarations_array_info:
                    if not node.identifier.index:
                        raise Exception(f"Array '{node.identifier.name}' must be accessed with an index")
                    base_location, start_index, size, offset = procedure_it.declarations_array_info[node.identifier.name]
                    self.add_instruction(f"STORE 1")
                    if isinstance(node.identifier.index, ValueNode):
                        self.add_instruction(f"STORE {self.get_memory_location(node.identifier, procedure_it)}")
                        return
                    self.load_procedure_array_memory_location_by_index(node.identifier, procedure_it)
                    self.add_instruction(f"ADD {base_location + size}") #add index to offset
                    self.add_instruction(f"STORE {POINTER_HANDLING_ADDR}")
                    self.add_instruction(f"LOAD 1")
                    self.add_instruction(f"STOREI {POINTER_HANDLING_ADDR}")
                else:
                    if node.identifier.index:
                        raise Exception(f"Variable '{node.identifier.name}' is not an array")
                    procedure_it.declaration_is_declared.add(node.identifier.name)
                    self.add_instruction(f"STORE {self.get_memory_location(node.identifier, procedure_it)}")
            else:
                raise Exception(f"\"{node.identifier.name}\" Undeclared (0x0004)")

    def gen_IfNode(self, node):
        else_label = self.new_label()
        end_label = self.new_label()
        self.generate(node.condition)
        self.add_label(else_label)
        self.add_instruction(f"JZERO {else_label}")
        self.generate(node.then_commands)
        self.add_label(end_label)
        self.add_instruction(f"JUMP {end_label}")
        self.add_placeholder(else_label)
        if node.else_commands:
            self.generate(node.else_commands)
        self.add_placeholder(end_label)

    def gen_WhileNode(self, node):
        start_label = self.new_label()
        end_label = self.new_label()

        self.add_placeholder(start_label)
        self.generate(node.condition)
        self.add_label(end_label)
        self.add_instruction(f"JZERO {end_label}")

        self.generate(node.commands)
        self.add_label(start_label)
        self.add_instruction(f"JUMP {start_label}")
        self.add_placeholder(end_label)

    def gen_RepeatUntilNode(self, node):
        start_label = self.new_label()
        self.add_placeholder(start_label)
        self.generate(node.commands)
        self.generate(node.condition)
        self.add_label(start_label)
        self.add_instruction(f"JZERO {start_label}")

    def gen_ForToNode(self, node):
        start_label = self.new_label()
        end_label = self.new_label()
        iterator_location = self.memory_counter
        self.generate(node.from_value)
        self.add_instruction(f"STORE {iterator_location}")

        if self.location[-1] == "main":
            self.foriterators[node.pidentifier.name] = iterator_location
            self.memory_counter += 1
            print(f"Iterator '{node.pidentifier.name}' allocated at memory location {self.foriterators[node.pidentifier.name]}")
        else:
            procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
            procedure_it.foriterators[node.pidentifier.name] = iterator_location
            self.memory_counter += 1
            print(f"Iterator '{node.pidentifier.name}' allocated at memory location {procedure_it.foriterators[node.pidentifier.name]}")


        to_value_location = self.memory_counter
        self.memory_counter += 1
        self.generate(node.to_value)
        self.add_instruction(f"STORE {to_value_location}")

        self.add_placeholder(start_label)
        self.add_instruction(f"LOAD {iterator_location}")
        self.add_instruction(f"SUB {to_value_location}")
        self.add_label(end_label)
        self.add_instruction(f"JPOS {end_label}")
        self.generate(node.commands)
        self.add_instruction(f"LOAD {iterator_location}")
        self.add_instruction(f"ADD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {iterator_location}")
        self.add_label(start_label)
        self.add_instruction(f"JUMP {start_label}")
        self.add_placeholder(end_label)

        if self.location[-1] == "main":
            del self.foriterators[node.pidentifier.name]
        else:
            procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
            del procedure_it.foriterators[node.pidentifier.name]

    def gen_ForDownToNode(self, node):
        start_label = self.new_label()
        end_label = self.new_label()
        iterator_location = self.memory_counter
        self.generate(node.from_value)
        self.add_instruction(f"STORE {iterator_location}")
        if self.location[-1] == "main":
            self.foriterators[node.pidentifier.name] = iterator_location
            self.memory_counter += 1
            print(f"Iterator '{node.pidentifier.name}' allocated at memory location {self.foriterators[node.pidentifier.name]}")
        else:
            procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
            procedure_it.foriterators[node.pidentifier.name] = iterator_location
            self.memory_counter += 1
            print(f"Iterator '{node.pidentifier.name}' allocated at memory location {procedure_it.foriterators[node.pidentifier.name]}")
        to_value_location = self.memory_counter
        self.memory_counter += 1
        self.generate(node.to_value)
        self.add_instruction(f"STORE {to_value_location}")

        self.add_placeholder(start_label)
        self.add_instruction(f"LOAD {iterator_location}")
        self.add_instruction(f"SUB {to_value_location}")
        self.add_label(end_label)
        self.add_instruction(f"JNEG {end_label}")
        self.generate(node.commands)
        self.add_instruction(f"LOAD {iterator_location}")
        self.add_instruction(f"SUB {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {iterator_location}")
        self.add_label(start_label)
        self.add_instruction(f"JUMP {start_label}")
        self.add_placeholder(end_label)

        if self.location[-1] == "main":
            del self.foriterators[node.pidentifier.name]
        else:
            procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
            del procedure_it.foriterators[node.pidentifier.name]

    def gen_DeclarationsNode(self, node):
        for var in node.variables:
            if self.location[-1] == "main" and var.is_array_range:
                base_location = self.memory_counter
                size = var.end - var.start + 1
                self.variables[var.name] = base_location
                self.array_info[var.name] = (base_location, var.start, size, self.memory_counter-var.start)
                self.add_instruction(f"SET {self.memory_counter - var.start}")
                self.memory_counter += size
                self.add_instruction(f"STORE {self.memory_counter}")
                self.memory_counter += 1
                print(f"Array '{var.name}' allocated at memory location {base_location} with size {size} start {var.start} end {var.end} offset {base_location-var.start} (offset location {base_location+size})")
            elif self.location[-1] == "main":
                self.variables[var.name] = self.memory_counter
                self.memory_counter += 1
                print(f"Variable '{var.name}' allocated at memory location {self.variables[var.name]}")
            else:
                procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
                if var.is_array_range:
                    base_location = self.memory_counter
                    size = var.end - var.start + 1
                    procedure_it.declarations[var.name] = base_location
                    procedure_it.declarations_array_info[var.name] = (base_location, var.start, size, self.memory_counter-var.start)
                    self.add_instruction(f"SET {self.memory_counter - var.start}")
                    self.memory_counter += size
                    self.add_instruction(f"STORE {self.memory_counter}")
                    self.memory_counter += 1
                    print(f"Array '{var.name}' allocated at memory location {base_location} with size {size} start {var.start} end {var.end} offset {base_location-var.start} (offset location {base_location+size})")
                else:
                    procedure_it.declarations[var.name] = self.memory_counter
                    self.memory_counter += 1
                    print(f"Variable '{var.name}' allocated at memory location {procedure_it.declarations[var.name]}")

    def gen_ProcedureNode(self, node):
        self.location.append(f"{node.procedure_head.procedure_name}")
        procedureinfo = self.Procedure()
        procedureinfo.jump_address = len(self.instructions)
        procedureinfo.address = self.memory_counter
        procedureinfo.name = node.procedure_head.procedure_name

        self.procedures.append(procedureinfo)
        self.memory_counter += 1
        self.generate(node.procedure_head)
        
        if node.declarations:
            for declaration in node.declarations.variables:
                if declaration.name in procedureinfo.arguments:
                    raise Exception(f"Identifier \"{declaration.name}\" already declared as argument")
            self.generate(node.declarations)
                
        self.generate(node.commands)
        self.add_instruction(f"RTRN {procedureinfo.address}")
        self.location.pop()

    def gen_ProcedureHeadNode(self, node):
        for arg in node.arguments_declaration.args:
            self.generate(arg)
            procedure_it = next((p for p in self.procedures if p.name == node.procedure_name), None)
            if arg.is_array:
                procedure_it.argument_is_array.add(arg.argument_name)
            procedure_it.arguments[arg.argument_name] = self.memory_counter #offset or address of variable. memory counter is just filler
            self.memory_counter += 1

    def gen_ProceduresNode(self, node):
        for procedure in node.procedures:
            self.generate(procedure)

    def gen_ArgumentNode(self, node):
        pass

    def gen_ProcedureCallNode(self, node):
        procedure_it = next((p for p in self.procedures if p.name == node.procedure_name), None) #destination procedure
        if self.location[-1] == node.procedure_name:
            raise Exception(f"Recursive call to procedure \"{node.procedure_name}()\"")
        for indexo, argument in enumerate(node.arguments.arguments): #arguments names from calling place
            corresponding_key = list(procedure_it.arguments.keys())[indexo]
            destination_address = procedure_it.arguments[corresponding_key]

            if argument.name in self.variables: # Check whole this if
                if argument.name in self.foriterators:
                    raise Exception(f"Iterator \"{argument.name}\" can't be procedure argument")
                elif argument.name in self.array_info:
                    if corresponding_key not in procedure_it.argument_is_array:
                        raise Exception(f"Procedure {procedure_it.name}() - argument on {indexo} position should not be array")
                    _, _, _, offset= self.array_info[argument.name]
                    self.add_instruction(f"SET {offset}")
                    self.add_instruction(f"STORE {destination_address}")
                else:
                    if corresponding_key in procedure_it.argument_is_array:
                        raise Exception(f"Procedure {procedure_it.name}() - argument on {indexo} position should be array")
                    self.add_instruction(f"SET {self.variables[argument.name]}")
                    self.add_instruction(f"STORE {destination_address}")
            else:
                calling_procedure_it = next((p for p in self.procedures if p.name == self.location[-1]), None)
                if argument.name in calling_procedure_it.arguments:
                    if argument.name in calling_procedure_it.argument_is_array:
                        if corresponding_key not in procedure_it.argument_is_array:
                            raise Exception(f"Procedure {procedure_it.name}() - argument on {indexo} position should not be array")
                    else:
                        if corresponding_key in procedure_it.argument_is_array:
                            raise Exception(f"Procedure {procedure_it.name}() - argument on {indexo} position should be array")
                    self.add_instruction(f"LOAD {calling_procedure_it.arguments[argument.name]}")
                    self.add_instruction(f"STORE {destination_address}")
                elif argument.name in calling_procedure_it.declarations:
                    if argument.name in calling_procedure_it.declarations_array_info:
                        if corresponding_key not in procedure_it.argument_is_array:
                            raise Exception(f"Procedure {procedure_it.name}() - argument on {indexo} position should not be array")
                        _, _, _, offset= calling_procedure_it.declarations_array_info[argument.name]
                        self.add_instruction(f"SET {offset}")
                        self.add_instruction(f"STORE {destination_address}")
                    else:
                        if corresponding_key in procedure_it.argument_is_array:
                            raise Exception(f"Procedure {procedure_it.name}() - argument on {indexo} position should be array")
                        self.add_instruction(f"SET {calling_procedure_it.declarations[argument.name]}")
                        self.add_instruction(f"STORE {destination_address}")
                elif argument.name in calling_procedure_it.foriterators:
                    raise Exception(f"Iterator \"{argument.name}\" can't be procedure argument")
                else:
                    raise Exception(f"Identifier \"{argument.name}\" undeclared (0x0005)")

        self.add_instruction(f"SET {len(self.instructions) + 3}")
        self.add_instruction(f"STORE {procedure_it.address}")
        jumpoffset = procedure_it.jump_address - len(self.instructions)
        self.add_instruction(f"JUMP {jumpoffset}")

    def gen_WriteNode(self, node):
        if isinstance(node.value, ValueNode):
            self.add_instruction(f"SET {node.value.value}")
            self.add_instruction(f"PUT 0")
        elif node.value.name in self.array_info:
            if not node.value.index:
                raise Exception(f"Array '{node.value.name}' must be accessed with an index")                
            if isinstance(node.value.index, ValueNode):
                self.generate(node.value)
                self.add_instruction(f"PUT 0")
                # self.add_instruction(f"PUT {self.get_memory_location(node.value)}")
            elif isinstance(node.value.index, IdentifierNode): 
                self.generate(node.value)
                self.add_instruction(f"PUT 0")
        elif node.value.name in self.variables:
            if node.value.index:
                raise Exception(f"Variable '{node.value.name}' is not an array")
            self.add_instruction(f"PUT {self.get_memory_location(node.value)}")
        else:
            self.generate(node.value)
            self.add_instruction(f"PUT 0")

        
    def gen_ReadNode(self, node):
        # procedure_it.declaration_is_declared.add(node.identifier.name)
        self.add_instruction(f"GET {self.get_memory_location(node.identifier)}")

    def gen_ValueNode(self, node):
        self.add_instruction(f"SET {node.value}")

    def gen_BinaryExpressionNode(self, node):
        # do akumulatora
        if node.operation == "+":
            self.gen_add(node)
        elif node.operation == "-":
            self.gen_substract(node)
        elif node.operation == "*":
            self.gen_multiply(node)
        elif node.operation == "/":
            self.gen_divide(node)
        elif node.operation == "%":
            self.gen_modulo(node)

    def gen_add(self, node):
        if isinstance(node.left, ValueNode) and isinstance(node.right, ValueNode):
            result = node.left.value + node.right.value
            self.add_instruction(f"SET {result}")
        elif isinstance(node.left, ValueNode) and isinstance(node.right, IdentifierNode):
            self.add_instruction(f"SET {node.left.value}")
            self.add_instruction(f"STORE 1")
            self.generate(node.right)
            self.add_instruction(f"ADD 1")
        elif isinstance(node.left, IdentifierNode) and isinstance(node.right, ValueNode):
            self.add_instruction(f"SET {node.right.value}")
            self.add_instruction(f"STORE 1")
            self.generate(node.left)
            self.add_instruction(f"ADD 1")
        else:
            self.generate(node.left)
            self.add_instruction(f"STORE 1")
            self.generate(node.right)
            self.add_instruction(f"ADD 1")

    def gen_substract(self, node):
        if isinstance(node.left, ValueNode) and isinstance(node.right, ValueNode):
            result = node.left.value - node.right.value
            self.add_instruction(f"SET {result}")
        elif isinstance(node.left, ValueNode) and isinstance(node.right, IdentifierNode):
            self.add_instruction(f"SET {node.left.value}")
            self.add_instruction(f"STORE 1")
            self.generate(node.right)
            self.add_instruction(f"STORE 2")
            self.add_instruction(f"LOAD 1")
            self.add_instruction(f"SUB 2")
        elif isinstance(node.left, IdentifierNode) and isinstance(node.right, ValueNode):
            self.add_instruction(f"SET {node.right.value}")
            self.add_instruction(f"STORE 1")
            self.generate(node.left)
            self.add_instruction(f"SUB 1")
        else:
            self.generate(node.right)
            self.add_instruction(f"STORE 1")
            self.generate(node.left)
            self.add_instruction(f"SUB 1")

    def gen_multiply(self, node):
        left = 1
        right = 2
        sign = 3
        counter = 4
        product = 5
        if isinstance(node.left, ValueNode) and isinstance(node.right, ValueNode):
            result = node.left.value * node.right.value
            self.add_instruction(f"SET {result}")
            return
        elif isinstance(node.left, ValueNode) and isinstance(node.right, IdentifierNode):
            self.add_instruction(f"SET {node.left.value}")
            self.add_instruction(f"STORE {left}")
            self.generate(node.right)
            self.add_instruction(f"STORE {right}")
        elif isinstance(node.left, IdentifierNode) and isinstance(node.right, ValueNode):
            self.generate(node.left)
            self.add_instruction(f"STORE {left}")
            self.add_instruction(f"SET {node.right.value}")
            self.add_instruction(f"STORE {right}")
        else:
            self.generate(node.left)
            self.add_instruction(f"STORE {left}")
            self.generate(node.right)
            self.add_instruction(f"STORE {right}")
        
        # Check if one of the values is 0
        self.add_instruction(f"LOAD {left}")
        self.add_instruction(f"JZERO 45")  #JZERO
        self.add_instruction(f"LOAD {right}")
        self.add_instruction(f"JZERO 43")   #JZERO

        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {sign}")
        self.add_instruction(f"STORE {counter}")
        self.add_instruction(f"STORE {product}")

        # Check sign of right value
        self.add_instruction(f"LOAD {right}")
        self.add_instruction(f"JPOS 7")    #JPOS
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {sign}")
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {right}")
        self.add_instruction(f"STORE {right}")

        # Check sign of left value
        self.add_instruction(f"LOAD {left}")
        self.add_instruction(f"JPOS 7")    #JPOS
        self.add_instruction(f"LOAD {sign}")
        self.add_instruction(f"ADD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {sign}")
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {left}")
        self.add_instruction(f"STORE {left}")

        self.add_instruction(f"LOAD {left}")
        self.add_instruction(f"JZERO 15")
        self.add_instruction(f"HALF")
        self.add_instruction(f"ADD 0")
        self.add_instruction(f"SUB {left}")
        self.add_instruction(f"JZERO 4")

        self.add_instruction(f"LOAD {right}")
        self.add_instruction(f"ADD {product}")
        self.add_instruction(f"STORE {product}")

        self.add_instruction(f"LOAD {left}")
        self.add_instruction(f"HALF")
        self.add_instruction(f"STORE {left}")

        self.add_instruction(f"LOAD {right}")
        self.add_instruction(f"ADD {right}")
        self.add_instruction(f"STORE {right}")

        self.add_instruction(f"JUMP -15")

        # Set sign
        # Counter == 0 -> result is positive
        # Counter == -1 -> result is negative
        # Counter == 1 -> result is negative 
        self.add_instruction(f"LOAD {sign}")
        self.add_instruction(f"JZERO 4")   #JZERO
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {product}")
        self.add_instruction(f"JUMP 2")    #JUMP

        self.add_instruction(f"LOAD {product}")

    def divide(self, dividend, divisor):
        return dividend // divisor if divisor !=0 else 0

    def gen_divide(self, node):
        dividend = 1
        divisor = 2
        sign = 3
        result_temp = 4
        currentDivisor = 5
        currentQuotient = 6

        if isinstance(node.left, ValueNode) and isinstance(node.right, ValueNode):
            result = self.divide(node.left.value, node.right.value)
            self.add_instruction(f"SET {result}")
            return
        elif isinstance(node.left, ValueNode) and isinstance(node.right, IdentifierNode):
            self.add_instruction(f"SET {node.left.value}")
            self.add_instruction(f"STORE {dividend}")
            self.generate(node.right)
            self.add_instruction(f"STORE {divisor}")
        elif isinstance(node.left, IdentifierNode) and isinstance(node.right, ValueNode):
            self.generate(node.left)
            self.add_instruction(f"STORE {dividend}")
            self.add_instruction(f"SET {node.right.value}")
            self.add_instruction(f"STORE {divisor}")
        else:
            self.generate(node.left)
            self.add_instruction(f"STORE {dividend}")
            self.generate(node.right)
            self.add_instruction(f"STORE {divisor}")

        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"JZERO 70")
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"JZERO 68")

        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {sign}")
        self.add_instruction(f"STORE {result_temp}")

        # if divident < 0
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"JPOS 8")
        self.add_instruction(f"JZERO 7")
        self.add_instruction(f"LOAD {sign}")
        self.add_instruction(f"SUB {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {sign}")
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {dividend}")
        self.add_instruction(f"STORE {dividend}")

        # if divisor < 0
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"JPOS 8")
        self.add_instruction(f"JZERO 7")
        self.add_instruction(f"LOAD {sign}")
        self.add_instruction(f"ADD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {sign}")
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {divisor}")
        self.add_instruction(f"STORE {divisor}")

        # Initialize temporary memory locations
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"STORE {currentDivisor}")  # Current divisor
        self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {currentQuotient}")  # Current quotient

        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {currentDivisor}")
        self.add_instruction(f"JNEG 8")  # Jump to adjust divisor if dividend < divisor
        self.add_instruction(f"LOAD {currentDivisor}")
        self.add_instruction(f"ADD {currentDivisor}")
        self.add_instruction(f"STORE {currentDivisor}")
        self.add_instruction(f"LOAD {currentQuotient}")
        self.add_instruction(f"ADD {currentQuotient}")
        self.add_instruction(f"STORE {currentQuotient}")
        self.add_instruction(f"JUMP -9")  # Loop back to adjust divisor and quotient

        self.add_instruction(f"LOAD {currentDivisor}")
        self.add_instruction(f"HALF")
        self.add_instruction(f"STORE {currentDivisor}")  # Shift divisor right

        self.add_instruction(f"LOAD {currentQuotient}")
        self.add_instruction(f"HALF")
        self.add_instruction(f"STORE {currentQuotient}")  # Shift quotient right

        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {currentDivisor}")
        self.add_instruction(f"STORE {dividend}")

        self.add_instruction(f"LOAD {result_temp}")
        self.add_instruction(f"ADD {currentQuotient}")
        self.add_instruction(f"STORE {result_temp}")  # Add current quotient to result

        # Reset divisor and quotient for next iteration
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"STORE {currentDivisor}")

        self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {currentQuotient}")

        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {currentDivisor}")
        self.add_instruction(f"JNEG 2")  # End loop if dividend < divisor

        self.add_instruction(f"JUMP -33")  # Repeat division loop 54

        # check sign
        self.add_instruction(f"LOAD {sign}")
        self.add_instruction(f"JZERO 10")
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"JNEG 5")
        self.add_instruction(f"JZERO 4")
        self.add_instruction(f"LOAD {result_temp}")
        self.add_instruction(f"ADD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {result_temp}")
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {result_temp}")
        self.add_instruction(f"STORE {result_temp}")

        self.add_instruction(f"LOAD {result_temp}")

    def modulo(self, dividend, divisor):
        return dividend % divisor if divisor != 0 else 0

    def gen_modulo(self, node):
        dividend = 1
        divisor = 2
        leftSign = 3
        rightSign = 4
        currentDivisor = 5

        if isinstance(node.left, ValueNode) and isinstance(node.right, ValueNode):
            result = self.modulo(node.left.value, node.right.value)
            self.add_instruction(f"SET {result}")
            return
        elif isinstance(node.left, ValueNode) and isinstance(node.right, IdentifierNode):
            self.add_instruction(f"SET {node.left.value}")
            self.add_instruction(f"STORE {dividend}")
            self.generate(node.right)
            self.add_instruction(f"STORE {divisor}")
        elif isinstance(node.left, IdentifierNode) and isinstance(node.right, ValueNode):
            self.generate(node.left)
            self.add_instruction(f"STORE {dividend}")
            self.add_instruction(f"SET {node.right.value}")
            self.add_instruction(f"STORE {divisor}")
        else:
            self.generate(node.left)
            self.add_instruction(f"STORE {dividend}")
            self.generate(node.right)
            self.add_instruction(f"STORE {divisor}")

        # Check if divisor is zero
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"JZERO 55")

        # Check if dividend is zero
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"JZERO 53")

        # Determine the sign of the dividend
        self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
        self.add_instruction(f"SUB {dividend}")
        self.add_instruction(f"JPOS 4")
        self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {leftSign}")
        self.add_instruction(f"JUMP 4")
        self.add_instruction(f"STORE {dividend}")
        self.add_instruction(f"LOAD {MINUS_ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {leftSign}")

        # Determine the sign of the divisor
        self.add_instruction(f"SET 0")
        self.add_instruction(f"SUB {divisor}")
        self.add_instruction(f"JPOS 4")
        self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {rightSign}")
        self.add_instruction(f"JUMP 4")
        self.add_instruction(f"STORE {divisor}")
        self.add_instruction(f"LOAD {MINUS_ONE_CONSTANT_ADDR}")
        self.add_instruction(f"STORE {rightSign}")

        # Initialize current divisor
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"STORE {currentDivisor}")

        # Modulo computation loop
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {divisor}")
        self.add_instruction(f"JNEG 17")
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {currentDivisor}")
        self.add_instruction(f"JNEG 5")
        self.add_instruction(f"LOAD {currentDivisor}")
        self.add_instruction(f"ADD {currentDivisor}")
        self.add_instruction(f"STORE {currentDivisor}")
        self.add_instruction(f"JUMP -6")
        self.add_instruction(f"LOAD {currentDivisor}")
        self.add_instruction(f"HALF")
        self.add_instruction(f"STORE {currentDivisor}")
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {currentDivisor}")
        self.add_instruction(f"STORE {dividend}")
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"STORE {currentDivisor}")
        self.add_instruction(f"JUMP -18")
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"JZERO 12")

        # Adjust the sign of the result
        self.add_instruction(f"LOAD {leftSign}")
        self.add_instruction(f"JPOS 4")
        self.add_instruction(f"LOAD {divisor}")
        self.add_instruction(f"SUB {dividend}")
        self.add_instruction(f"STORE {dividend}")
        self.add_instruction(f"LOAD {rightSign}")
        self.add_instruction(f"JPOS 4")
        self.add_instruction(f"LOAD {dividend}")
        self.add_instruction(f"SUB {divisor}")
        self.add_instruction(f"STORE {dividend}")

        # Final result
        self.add_instruction(f"LOAD {dividend}")

    def gen_ConditionNode(self, node):
        self.generate(node.left_value)
        self.add_instruction(f"STORE 1")
        self.generate(node.right_value)
        self.add_instruction(f"SUB 1")

        if node.operation == "<":
            self.add_instruction(f"JPOS 3")
            self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")    
            self.add_instruction(f"JUMP 2")
            self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        elif node.operation == ">":
            self.add_instruction(f"JNEG 3")
            self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")
            self.add_instruction(f"JUMP 2")
            self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        elif node.operation == "=":
            self.add_instruction(f"JZERO 3")
            self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")           
            self.add_instruction(f"JUMP 2")
            self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
        elif node.operation == "!=":
            self.add_instruction(f"JZERO 3")
            self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
            self.add_instruction(f"JUMP 2")
            self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")           
        elif node.operation == "<=":
            self.add_instruction(f"JNEG 3")
            self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
            self.add_instruction(f"JUMP 2")
            self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")    
        elif node.operation == ">=":
            self.add_instruction(f"JPOS 3")
            self.add_instruction(f"LOAD {ONE_CONSTANT_ADDR}")
            self.add_instruction(f"JUMP 2")
            self.add_instruction(f"LOAD {ZERO_CONSTANT_ADDR}")

    def gen_IdentifierNode(self, node):
        if node.name in self.array_info:
            if not node.index:
                raise Exception(f"Array '{node.name}' must be accessed with an index")
            if isinstance(node.index, ValueNode):
                self.add_instruction(f"LOAD {self.get_memory_location(node)}")
            elif isinstance(node.index, IdentifierNode):
                self.add_instruction(f"LOADI {self.get_memory_location(node)}")
        elif node.name in self.variables:
            if node.index:
                raise Exception(f"Variable '{node.name}' is not an array")
            self.add_instruction(f"LOAD {self.get_memory_location(node)}")
        elif node.name in self.foriterators:
            self.add_instruction(f"LOAD {self.get_memory_location(node)}")
        else: #in procedure
            procedure_it = next((p for p in self.procedures if self.location[-1] == p.name), None)
            if not procedure_it:
                raise Exception(f"\"{node.name}\" Undeclared (0x0006)")
            if node.name in procedure_it.foriterators:
                self.add_instruction(f"LOAD {self.get_memory_location(node, procedure_it)}")
            elif node.name in procedure_it.arguments:
                if node.name in procedure_it.argument_is_array:
                    if not node.index:
                        raise Exception(f"Array '{node.name}' must be accessed with an index")
                else:
                    if node.index:
                        raise Exception(f"Variable '{node.name}' is not an array")
                self.add_instruction(f"LOADI {self.get_memory_location(node, procedure_it)}")
            elif node.name in procedure_it.declarations:
                if node.name in procedure_it.declarations_array_info:
                    if not node.index:
                        raise Exception(f"Array '{node.name}' must be accessed with an index")
                    if isinstance(node.index, ValueNode):
                        self.add_instruction(f"LOAD {self.get_memory_location(node, procedure_it)}")
                    else:
                        self.add_instruction(f"LOADI {self.get_memory_location(node, procedure_it)}")
                else:
                    if node.index:
                        raise Exception(f"Variable '{node.name}' is not an array")
                    self.add_instruction(f"LOAD {self.get_memory_location(node, procedure_it)}")
            else:
                raise Exception(f"\"{node.name}\" Undeclared (0x0009)")

    def get_array_offset(self, node):
        _, _, _, offset = self.array_info[node.name]
        self.add_instruction(f"ADD {offset}")
        self.add_instruction(f"STORE {offset + node.index.value}")
        if node.name in self.array_info:
            return offset
        return offset

    def get_memory_location(self, node, procedure_it = None):
        if node.name in self.array_info:
            if isinstance(node.index, ValueNode):
                base_location, start_index, _, _= self.array_info[node.name]
                return base_location + node.index.value - start_index
            elif isinstance(node.index, IdentifierNode):
                return self.get_array_memory_location_by_index_name(node)
        elif node.name in self.variables:
            return self.variables[node.name]
        elif node.name in self.foriterators:
            return self.foriterators[node.name]
        # procedures
        elif node.name in procedure_it.foriterators:
            return procedure_it.foriterators[node.name]
        elif node.name in procedure_it.arguments:
            if node.name in procedure_it.argument_is_array:
                if isinstance(node.index, ValueNode):
                    self.add_instruction(f"SET {node.index.value}")
                self.load_procedure_array_memory_location_by_index(node, procedure_it)
                self.add_instruction(f"STORE 2") #index
                self.add_instruction(f"LOAD {procedure_it.arguments[node.name]}")
                self.add_instruction(f"ADD 2") #add index to offset
                self.add_instruction(f"STORE {POINTER_HANDLING_ADDR}")
                return POINTER_HANDLING_ADDR
            else:
                return procedure_it.arguments[node.name]
        elif node.name in procedure_it.declarations:
            if node.name in procedure_it.declarations_array_info:
                base_location, start_index, size, offset = procedure_it.declarations_array_info[node.name]
                if isinstance(node.index, ValueNode):
                    return offset + node.index.value
                self.load_procedure_array_memory_location_by_index(node, procedure_it)
                self.add_instruction(f"STORE 2") #index
                self.add_instruction(f"LOAD {base_location + size}")
                self.add_instruction(f"ADD 2") #add index to offset
                self.add_instruction(f"STORE {POINTER_HANDLING_ADDR}")
                return POINTER_HANDLING_ADDR
            else:
                return procedure_it.declarations[node.name]

    def get_array_memory_location_by_index_name(self, node):
        index_addr = self.get_memory_location(node.index)
        base_location, _, size, _ = self.array_info[node.name]
        self.add_instruction(f"LOAD {index_addr}")
        self.add_instruction(f"ADD {base_location + size}")
        self.add_instruction(f"STORE {POINTER_HANDLING_ADDR}")
        return POINTER_HANDLING_ADDR

    def load_procedure_array_memory_location_by_index(self, node, procedure_it):
        if isinstance(node.index, ValueNode):
            # Should be already handled
            return
        elif node.index.name in procedure_it.arguments:
            self.add_instruction(f"LOADI {procedure_it.arguments[node.index.name]}")
        elif node.index.name in procedure_it.declarations:
            self.add_instruction(f"LOAD {procedure_it.declarations[node.index.name]}")
        elif node.index.name in procedure_it.foriterators:
            self.add_instruction(f"LOAD {procedure_it.foriterators[node.index.name]}")
        else:
            raise Exception(f"\"{node.index.name}\" Undeclared (0x0007)")

    def get_code(self):
        self.resolve_placeholders()
        self.add_instruction("HALT")
        return "\n".join(self.instructions)