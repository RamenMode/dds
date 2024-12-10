from ...RingClient import RingClient
from typing import List
import sys

r = RingClient("ring-3", sys.argv[1])

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
            print(r.query(key))
        result = [r.query(word) for word in s]
        for key in keys:
            r.delete(key)
        return result
    
s = Solution()

input = ["fig","wag","rio","dew","ivy","key","chi","sis","sea","ups","rex","ode","ala","sop","tab","car","bmw","sop","try","ola","yum","zoe","age","pot","arc","spy","try","gig","bah","map","pal","kin","two","fin","doe","ali","rye","owl","cal","jew","pan","nil","mel","gem","who","son","mys","maj","sip","ken","did","why"]
output = s.groupAnagrams(input)
expect = [["did"],["ken"],["maj"],["son"],["mel"],["nil"],["pan"],["owl"],["fin"],["kin"],["map"],["ala"],["sip"],["who"],["tab"],["rio"],["jew"],["sop","sop"],["spy"],["sea"],["sis"],["chi"],["age"],["key"],["why"],["yum"],["cal"],["ali"],["doe","ode"],["pal"],["fig"],["mys"],["ups"],["arc","car"],["bah"],["gem"],["two"],["wag"],["bmw"],["gig"],["try","try"],["rye"],["rex"],["ivy"],["ola"],["zoe"],["dew"],["pot"]]
print("--------------------the answer is------------------------------------------------------------", output, len(output), len(expect))