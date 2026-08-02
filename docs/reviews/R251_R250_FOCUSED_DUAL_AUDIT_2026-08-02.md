# R-251 R-250 focused dual-audit record

Date: 2026-08-02

Status: **DUAL GO FOR AUTHORITY FREEZE; EXECUTION NO-GO**

## Reviewed evidence

Two independent auditors reviewed, without executing codec work:

- R-249 closure SHA-256
  `3287530dfe76810a0478276dd36d0c8ac025168cc7fe3f46f1cb16e704ba9e47`;
- R-250 preflight SHA-256
  `679b596411ace6d18621dc28c6c784acf0a25f31470b35d0db7a604a0aa5999f`;
- runner SHA-256
  `736c7aa6ccb5f6f562f091737a52a5b0dac0b963f9066bbd0247d1781dc7e8e5`,
  exactly 640 physical lines and 50,601 bytes.

Both returned GO for provenance commit only. After normalizing R-250 generation
identifiers to R-246 and reverting `str(profile_path)` to the failed expression,
the runner was byte-for-byte equal to the R-246 committed runner. Therefore the
only functional change is the documented filename conversion at the
`pstats.Stats` boundary. All machine-visible authority, request, worker,
receipt, failure schemas and terminal paths are consistently R-250.

The focused Python 3.14.6 check reproduced `TypeError` for `WindowsPath` and
successfully reopened and formatted the same profile after `str(Path)`. Codec,
oracle, native core, test module and source WAV remain unchanged.

## Remaining gate

R-250 authority must bind the published commit, exact runner, R-249 closure,
R-250 preflight, this audit, inherited R-246 architecture evidence, and the
unchanged complete runtime/source closure. Both auditors must return binary GO
over the exact runner-authority pair before one public invocation. No blind
retry is authorized.

