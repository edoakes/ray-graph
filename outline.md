# Introduction
- [stephanie]Ray is a framework for distributed Python with a low-level API
- [ed]Problem: Can we support specific applications (e.g., stream processing) with a low-level API like Ray's?
- [ed]stream processing application example
# [stephanie]Background
- [code]Ray API
- [figure]Ray architecture and scheduler
- [code][figure]stream processing application example
# Design
- [ed]IR
  - [code]stream processing application example written in the IR
  - Semi-lazy evaluation
  - "Group" dependencies to mimic BSP
  - Actor scheduling
- [stephanie][pseudocode]Scheduler algorithm for group scheduling
# [stephanie]Evaluation
- [figure(plot against data size, CDF)]Comparison against vanilla Ray scheduler
# [ed]Discussion/Future work
- Static analysis to automatically infer the IR from pure Ray code
  - Recognizing data dependency patterns
  - Recognizing evaluation points
- Extending the IR to support other data dependency patterns
- Designing an IR to support other features, e.g., garbage collection
