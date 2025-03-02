import subprocess
import re
import pytest

def strip_ansi_codes(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

@pytest.mark.parametrize("basic", [
    {
        "input_file": "../tests/basic_tests/example1.imp",
        "inputs": [12, 32],
        "expected_outputs": [3, 1, 4]
    },
    {
        "input_file": "../tests/basic_tests/example2.imp",
        "inputs": [0, 1],
        "expected_outputs": [46368, 28657]
    },
])

def test_compiler(basic, capsys):
    compiler = "compiler.py"
    virtual_machine = "../maszyna_wirtualna/maszyna-wirtualna"
    output_file = "../out/" + basic["input_file"].split("/")[-1].replace(".imp", ".mr")

    subprocess.run(["python", compiler, basic["input_file"], output_file], check=True)

    input_values = "\n".join(map(str, basic["inputs"])) + "\n"
    process = subprocess.run([virtual_machine, output_file], input=input_values, text=True, capture_output=True)

    output_lines = process.stdout.splitlines()

    actual_outputs = [
        int(match.group(1))
        for line in output_lines
        if (match := re.search(r">\s*(\d+)", line))  # Use match assignment
    ]
    assert actual_outputs == basic["expected_outputs"]

    complexity = re.search(r"koszt:\s*([\d,]+)", strip_ansi_codes(output_lines[-1])).group(1)
    io = re.search(r"i/o:\s*([\d,]+)", strip_ansi_codes(output_lines[-1])).group(1)

    with capsys.disabled():
        print(f"\n{basic["input_file"].split("/")[-1]}")
        print(f"Input:  {basic["inputs"]}")
        print(f"Output: {actual_outputs}")
        if complexity and io:
            print("Complexity cost: " + complexity + "; including i/o: " + io)
        else:
            print("Complexity not found")

