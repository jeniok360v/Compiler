import subprocess
import re
import pytest

def strip_ansi_codes(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

test_cases = {
    "basic": [
        {"input_file": "../tests/basic_tests/example1.imp", "inputs": [12, 32], "expected_outputs": [3, 1, 4]},
        {"input_file": "../tests/basic_tests/example2.imp", "inputs": [0, 1], "expected_outputs": [46368, 28657]},
        {"input_file": "../tests/basic_tests/example3.imp", "inputs": [1], "expected_outputs": [121393]},
        {"input_file": "../tests/basic_tests/example4.imp", "inputs": [20, 9], "expected_outputs": [167960]},
        {"input_file": "../tests/basic_tests/example5.imp", "inputs": [1234567890, 1234567890987654321, 987654321], "expected_outputs": [674106858]},
        {"input_file": "../tests/basic_tests/example6.imp", "inputs": [20], "expected_outputs": [2432902008176640000, 6765]},
        {"input_file": "../tests/basic_tests/example7.imp", "inputs": [0, 0, 0], "expected_outputs": [31000, 40900, 2222010]},
        {"input_file": "../tests/basic_tests/example8.imp", "inputs": [], "expected_outputs": [5, 2, 10, 4, 20, 8, 17, 16, 11, 9, 22, 18, 21, 13, 19, 3, 15, 6, 7, 12, 14, 1, 0, 1234567890, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]},
        {"input_file": "../tests/basic_tests/example9.imp", "inputs": [20, 9], "expected_outputs": [167960]},
        {"input_file": "../tests/basic_tests/exampleA-n.imp", "inputs": [], "expected_outputs": [25, 48, 69, 88, 105, 120, 133, 144, 153, 160, 165, 168, 169, 168, 165, 160, 153, 144, 133, 120, 105, 88, 69, 48, 25]},
        {"input_file": "../tests/basic_tests/program0.imp", "inputs": [5323], "expected_outputs": [1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1]},
        {"input_file": "../tests/basic_tests/program1.imp", "inputs": [34, 51, -119, 187], "expected_outputs": [17]},
        {"input_file": "../tests/basic_tests/program2.imp", "inputs": [], "expected_outputs": [97, 89, 83, 79, 73, 71, 67, 61, 59, 53, 47, 43, 41, 37, 31, 29, 23, 19, 17, 13, 11, 7, 5, 3, 2]},
        {"input_file": "../tests/basic_tests/program3.imp", "inputs": [12345678903], "expected_outputs": [3, 1, 4115226301, 1]},
    ],
    "advanced": [
        {"input_file": "../tests/advanced_tests/example_adv_0.imp", "inputs": [], "expected_outputs": [102, 103, 104, 105, 106, 107, 108, 109, 110, 104, 105, 106]},
    ],
}

all_tests = [
    pytest.param(case, marks=pytest.mark.basic) for case in test_cases["basic"]
] + [
    pytest.param(case, marks=pytest.mark.advanced) for case in test_cases["advanced"]
]

@pytest.mark.parametrize("test_case", all_tests)
def test_program(test_case, capsys):
    input_file = test_case["input_file"]
    inputs = test_case["inputs"]
    expected_outputs = test_case["expected_outputs"]

    compiler = "compiler.py"
    virtual_machine = "../maszyna_wirtualna/maszyna-wirtualna"
    output_file = "../out/" + input_file.split("/")[-1].replace(".imp", ".mr")

    subprocess.run(["python", compiler, input_file, output_file], check=True)

    input_values = "\n".join(map(str, inputs)) + "\n"
    process = subprocess.run([virtual_machine, output_file], input=input_values, text=True, capture_output=True)

    output_lines = process.stdout.splitlines()

    actual_outputs = [
        int(match.group(1))
        for line in output_lines
        if (match := re.search(r">\s*(\d+)", line))  # Use match assignment
    ]
    assert actual_outputs == expected_outputs

    complexity = re.search(r"koszt:\s*([\d,]+)", strip_ansi_codes(output_lines[-1])).group(1)
    io = re.search(r"i/o:\s*([\d,]+)", strip_ansi_codes(output_lines[-1])).group(1)

    with capsys.disabled():
        print(f"\n{input_file.split("/")[-1]}")
        print(f"Input:  {inputs}")
        print(f"Output: {actual_outputs}")
        if complexity and io:
            print("Complexity cost: " + complexity + "; including i/o: " + io)
        else:
            print("Complexity not found")

