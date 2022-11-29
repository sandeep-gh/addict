# addict with change tracker

A modified addict to track changes to values of fields in addict. 

Caution:Note: Not all tests are passing

## Usage:

```python
mydict = Dict()

mydict.a.b.c = 15

for _ in mydict.get_changed_history():
    print(_) 
```
The output
```
.a.b.c
```

Use clear_changed_history to clear all changed history.

```
mydict.clear_changed_history()
for _ in mydict.get_changed_history():
    print(_)
```
outputs empty. 

## Key Points

1. Only tracks changes in values. Field additions and deletions are not being tracked. 
2. Every field keeps a `__tracker` variable to keep track of all its members that have changed. 


# TODO
1. History not valid after
pickle.load
2. building dict from another dict
following expression wont' work
```python
cjs_cfg = Dict(x, track_changes=True)
```

instead use
```python 
cjs_cfg = Dict(track_changes = True)
with open("cjs_cfg.pickle", "rb") as fh:
    x = pickle.load(fh)
for _ in oj.dictWalker(x):
    oj.dnew(cjs_cfg, _[0], _[1])

```
