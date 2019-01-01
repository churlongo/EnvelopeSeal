"""Rotation interval and overdue calculation.

A key declares a rotation interval in days. The key is overdue when the as-of
date is later than its created date plus that interval. The as-of date is passed
in explicitly, never read from the wall clock, so a run is deterministic and two
runs of the same manifest against the same as-of date are byte identical.

