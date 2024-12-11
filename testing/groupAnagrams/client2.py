from ...RingClient import RingClient
from typing import List
import sys
import json
import os

r = RingClient("ring23", sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0")

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        keys = []
        s = set()
        for word in strs:
            key = ''.join(sorted(word))
            s.add(key)
            value = r.query(key)
            if value:
                value.append(word)
            else:
                value = [word]
            r.update(key, value)
            keys.append(key)
            #print(r.query(key))
        result = [r.query(word) for word in s]
        for key in keys:
            r.delete(key)
        return result

def printResult(nodeId, result):
    print(f"node with id {nodeId} has result-----------------------------------")
    attributes = ["fingerTable", "nodeId", "host", "port", "successor", "predecessor", "storage", "ring_name"]
    for a, v in zip(attributes, result):
        print(f"{a} = {v}")

result = r.get_all(20)
printResult(20, result)
result = r.get_all(110)
printResult(110, result)
result = r.get_all(200)
printResult(200, result)
result = r.get_all(290)
printResult(290, result)

s = Solution()

index = 1
script_dir = os.path.dirname(os.path.abspath(__file__))
test_json_path = os.path.join(script_dir, "test.json")
with open(test_json_path, "r") as file:
    test = json.load(file)
    inputs = test["inputs"]
    expected = test["expected"]

    for input, expect in zip(inputs, expected):
        print(f"--------------------------------------Test Case {index}--------------------------------------")
        
        output = s.groupAnagrams(input)

        output = sorted([sorted(inner) for inner in output])
        expect = sorted([sorted(inner) for inner in expect])

        print(f"output is {output}")
        print(f"expected is {expect}")

        same =  output == expect
        print(f"They are the same: {same}")
        index += 1


result = r.get_all(20)
printResult(20, result)
result = r.get_all(110)
printResult(110, result)
result = r.get_all(200)
printResult(200, result)
result = r.get_all(290)
printResult(290, result)