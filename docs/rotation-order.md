# Reading a rotation order

The planner prints a safe order derived from the hierarchy.

- Root keys come before the keys they wrap.
- Ties break on key name, so two runs produce the same order.
- A key in the blast radius of a scheduled rotation is listed once, even when
  two parents reach it.

The order is a plan, not an action. EnvelopeSeal never touches key material.
