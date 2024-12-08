from ...RingClient import RingClient
from typing import List

r = RingClient("ring2")

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        keys = []
        for word in strs:
            key = ''.join(sorted(word))
            r.update(key, word)
            keys.append(key)
            print(r.query(key))
        result = [r.query(key) for key in keys]
        for key in keys:
            r.delete(key)
        return result
    
s = Solution()

s.groupAnagrams(["eat","tea","tan","ate","nat","bat"])