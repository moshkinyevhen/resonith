# R-197 Hard-Profile and Snapshot Gate

Status: **FOCUSED IMPLEMENTATION GATE PASSED**

This is an internal R-197 checkpoint, not acceptance of R-191, a codec
generation, a compression result, or a product claim.

Implemented scope:

- published R-190/R-191 hard ceilings;
- checked pointer ranges and pairwise no-alias validation;
- unchanged R-190 `output_count` on failures other than the declared
  insufficient-capacity result;
- bounded snapshots of resolutions, observations, edges, and manifests before
  semantic analysis;
- complete canonical R-190 comparison over the frozen snapshot;
- focused hard-bound, empty-input, overlap, canary, deterministic and
  independent-oracle regressions.

Focused evidence:

- Clang 22 / C++23 native build: passed;
- `resonith_partial_graph_test`: passed;
- independent Python fixed-point suite: `39 passed`;
- test wall time: 2.27 seconds for the Python suite.

The next dependency is the separate transactional v3 count/stage/commit ABI.
The complete R-197 kill gate remains pending.
