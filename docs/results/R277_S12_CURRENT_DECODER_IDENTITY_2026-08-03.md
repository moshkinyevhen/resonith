# R-277 Current-Decoder Identity Check

Date: 2026-08-03

Status: **FOCUSED OUTPUT-IDENTITY PASS; NOT A CODEC CHANGE**

The current strict C++23 Core DLL, SHA-256
`f22e3e002f15c811a250446fa08e586805d0cd7b88a8f362ad96e42af85326ba`,
decoded every retained R-221/S12 Resonith stream. All 19 decoded PCM16 payload
hashes exactly matched their independently audited R-221 receipts. The same
DLL decoded the retained 319.38-second R-220 long-speech stream to PCM16
SHA-256
`fefe12c2f5daf1df2ea1ff1cf623df55ad3f96629a21aca3fc77752fc58ab476`,
which also exactly matches its preserved receipt.

The 19 registered decodes completed in 45.2 seconds; the long-speech decode
completed in 6.6 seconds including Python process startup and hashing. This
check establishes output identity for existing S12 streams only. It does not
prove byte-identical re-encoding, compression improvement, or S19 admission.

The S12 lapped encoder, parser, entropy and native lapped source files used by
R-221 are byte-identical at the current revision. The current DLL differs
because later independent subsystems were added, so its exact binary identity
is frozen separately instead of being assumed from source history.
