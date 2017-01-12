"""Blast radius: how many data keys are reachable from each key encrypting key.

If a key encrypting key is compromised, every data key reachable from it by
following wrap edges is compromised too, because the attacker can unwrap them in
turn. The blast radius of a key encrypting key is the count of those data keys.
It is the single number that says how bad losing that one key would be.

Data keys are not reported here: their blast radius is themselves, which is not
useful for prioritising which key encrypting keys to protect hardest.
