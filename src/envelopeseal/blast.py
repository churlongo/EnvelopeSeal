"""Blast radius: how many data keys are reachable from each key encrypting key.

If a key encrypting key is compromised, every data key reachable from it by
following wrap edges is compromised too, because the attacker can unwrap them in
turn. The blast radius of a key encrypting key is the count of those data keys.
