import sys
from lexer import MyLexer
from parser import MyParser
from codegen import CodeGenerator

def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_file> <output_file>")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, 'r') as file:
            data = file.read()
    except FileNotFoundError:
        print(f"Failed to open file: {input_file}")
        return

    print("Parsing input...")
    lexer = MyLexer()
    parser = MyParser()
    try:
        tokens = list(lexer.tokenize(data))
        print("Tokens:")
        for token in tokens:
            print(token)
        root = parser.parse(iter(tokens))  # Convert list to iterator
        print("Parsing completed successfully.")
        if root:
            print("Generated AST:")
            root.print()
            codegen = CodeGenerator()
            codegen.generate(root)
            machine_code = codegen.get_code()
            with open(output_file, 'w') as file:
                file.write(machine_code)
            print(f"Machine code written to {output_file}")
        else:
            print("No AST generated.")
    except Exception as e:
        print(f"Parsing failed: {e}")

if __name__ == "__main__":
    main()