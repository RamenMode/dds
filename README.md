If you want to test, in the outside directory, run in module mode
```bash
python3 -m dds.testing.node1
python3 -m dds.testing.node2
python3 -m dds.testing.node3
python3 -m dds.testing.node4
python3 -m dds.testing.client1
python3 -m dds.testing.node7
python3 -m dds.testing.node5
```
In separate terminals.

Notice that nodes 1-4 just create a nice ring and join, then client1 adds some values, then node7 joins the chord, and node5 prints the contents of all nodes. Node7 joining should cause a value transfer. Observe fingertables and successors/predecessors. Should be correct.
