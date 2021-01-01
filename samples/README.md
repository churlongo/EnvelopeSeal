# Sample manifests

These two files are hand authored test vectors, not exported production key
material. They contain no real key bytes, only key ids, declared algorithms,
declared sizes, and declared dates. Nothing here can decrypt anything.

## healthy.manifest

A hierarchy that passes every check. One root, `root-hsm`, wraps two mid level
key encrypting keys, and each of those wraps two data keys. Every wrap protects
a key of equal or lower strength, so there is no inversion. There is no cycle.
