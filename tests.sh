#!/usr/bin/env bash

CONFIG_DIR="example_files"
TEST_DIR="test_outputs"
FINAL_RESULT=0

run_test() {
    local config="$CONFIG_DIR/$1"
    local output_file="$TEST_DIR/$2"
    local expected_result="$TEST_DIR/$3"

    echo -n "running test on $config..."
    python3 csvtransfer.py -o "$output_file" "$config" || FINAL_RESULT=1
    difference="$(diff "$output_file" "$expected_result")"

    if [[ "$difference" != "" ]]
    then
        echo "failed"
        echo "diff:"
        echo "$difference"
        FINAL_RESULT=1
    else
        echo "passed"
    fi
    echo "========================================"
}

run_test "config_example.ini"  "test1.csv" "expected1.csv"
run_test "config_example2.ini" "test2.csv" "expected2.csv"

echo "testing complete"
exit $FINAL_RESULT
