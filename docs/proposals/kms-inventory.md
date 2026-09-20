# Proposal: live KMS inventory

Status: closed, not planned for this tool.

Reading keys from a cloud KMS would need credentials, network error handling,
and a story for which snapshot an audit saw. The manifest already is that
snapshot; exporting it keeps every report reproducible from the files next to
it.
