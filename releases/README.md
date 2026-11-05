# EMTG IPOPT Runtime Archive

Extract this archive into `/opt/toolkit` to obtain:

```text
/opt/toolkit/emtg/bin/EMTGv9
```

Install the Debian packages in `RUNTIME_REQUIREMENTS.txt` before running EMTG.
Invoke the fixed executable with an options file and no shell:

```bash
/opt/toolkit/emtg/bin/EMTGv9 /opt/work/request.emtgopt
```

The archive includes base universe and standard public hardware data. The
third-party deployment environment must provide request-specific inputs and
mission SPICE kernels, keep them read-only where possible, and use an isolated
writable run directory for outputs.
