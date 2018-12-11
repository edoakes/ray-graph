# Introduction
Machine learning systems in production may require a diverse array of applications, requiring everything from hyperparameter search to train a model to stream processing to ingest data.
In the past, specialized systems have been built for each of these individual applications, leaving the burden of integrating these systems on the user, with a potentially prohibitive performance cost.
Ray is a system that makes it easy to develop and deploy applications in machine learning by exposing higher-level Python libraries for traditionally disparate applications, all supported by a common distributed framework.
Ray does this by exposing a relatively low-level API that is flexible enough to support a variety of computation patterns.
This API allows the user to define "tasks", which represent an asynchronous and possibly remote function invocation, and "actors", which represent some state bound to a process.

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
