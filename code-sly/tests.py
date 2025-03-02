import subprocess
import re

def strip_ansi_codes(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

compiler = "compiler.py"
virtual_machine = "../maszyna_wirtualna/maszyna-wirtualna"
input_file = "../tests/basic_tests/example1.imp"
output_file = "../out/example1.mr"

inputs = [12, 32]
expected_outputs = [3, 1, 4]

input_values = "\n".join(map(str, inputs)) + "\n"

try:
    compile_command = ["python", compiler, input_file, output_file]
    subprocess.run(compile_command, check=True)
    # print(f"Compilation successful: {input_file} -> {output_file}")
except subprocess.CalledProcessError as e:
    print(f"Error during compilation: {e}")
    exit(1)

try:
    run_command = [virtual_machine, output_file]
    process = subprocess.run(
        run_command,
        input=input_values,
        text=True,
        capture_output=True
    )

    output_lines = process.stdout.splitlines()

    actual_outputs = [
        int(match.group(1))
        for line in output_lines
        if (match := re.search(r">\s*(\d+)", line))  # Use match assignment
    ]

    complexity = re.search(r"koszt:\s*([\d,]+)", strip_ansi_codes(output_lines[-1])).group(1)
    io = re.search(r"i/o:\s*([\d,]+)", strip_ansi_codes(output_lines[-1])).group(1)

    print(f"Input:    {inputs}")
    print(f"Expected: {expected_outputs}")
    print(f"Actual:   {actual_outputs}")

    if complexity:
        print("Complexity cost: " + complexity)
    else:
        print("Complexity not found")

    if io:
        print("Including i/o:   " + io)
    else:
        print("I/O complexity not found")

    if actual_outputs == expected_outputs:
        print("Validation PASSED")
    else:
        print("Validation FAILED")

except subprocess.CalledProcessError as e:
    print(f"Error during execution: {e}")
    exit(1)


