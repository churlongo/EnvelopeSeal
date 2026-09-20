# Recipe: a scheduled hierarchy audit

`/etc/systemd/system/envelope-audit.service`:

```ini
[Unit]
Description=Envelope key hierarchy audit

[Service]
Type=oneshot
WorkingDirectory=/opt/keys
ExecStart=/usr/bin/python3 -m envelopeseal audit manifest.json --json
SuccessExitStatus=0 1
```

`SuccessExitStatus=0 1` treats findings as a successful run; the report is
the signal. Pair it with a timer that runs weekly and before every rotation
window.
