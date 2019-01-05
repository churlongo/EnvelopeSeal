"""Algorithm and key size ordering.

A wrapping key must be at least as strong as the key it protects. If a weaker
key wraps a stronger one, an attacker breaks the outer key at lower cost and
gains the inner key for free, so the declared inner strength is a fiction. That
is a strength inversion finding.

