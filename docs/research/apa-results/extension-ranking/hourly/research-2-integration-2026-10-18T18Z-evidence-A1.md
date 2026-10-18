# APA 18Z: contracts 01-10

01. Plan revision 182: 91 tasks; group acceptance remains partial.
02. Coordinator queue: reconciliation priority 100, provider verification 98.
03. PR164 stopped without automatic retry.
04. Reconciliation design checks SQLite journal read-only.
05. Reconciliation design compares 44 GUID and native signatures.
06. Old provider snapshot: version 1.5.8, 236 commands.
07. New snapshot: version 1.5.10, 262 commands.
08. New snapshot belongs to port 19723, not the affected 19724.
09. Router compares actual provider version with catalog version before mutation.
10. The original workflow refers to the newer catalog; cause of mismatch is not proven.

Source: https://github.com/dvikt33-ux/safe-bim-layer/pull/164
Each line is a source finding, not a runtime test. Next: exact active catalog and port-specific version.
