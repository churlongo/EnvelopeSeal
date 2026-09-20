# Cookbook: auditing a key hierarchy

Run this before a rotation and again after, then diff the two reports.

## 1. Audit the manifest

```
python -m envelopeseal audit manifest.json
```

The report prints the graph, the strength of each key, and the rotation
order. A wrapped key before its KEK is ordered topologically, so file order
never changes the result.

## 2. Read the blast radius before rotating

```
python -m envelopeseal graph manifest.json
```

The radius counts the keys reachable from each KEK. Rotate the smallest
radius first unless a strength finding says otherwise.

## 3. Attach both reports to the change

Reports are deterministic, so a before and after pair diff cleanly and show
exactly what the rotation touched.
