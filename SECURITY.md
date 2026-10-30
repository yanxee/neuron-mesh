# Security Policy

[English](SECURITY.md) | [简体中文](SECURITY.zh-CN.md)

Neuron Mesh is a research prototype. Do not expose the default configuration to the public Internet.

## Required before an external pilot

- Replace the development bearer token with per-node credentials and short-lived client tokens.
- Terminate TLS for the HTTP mesh, or replace it with libp2p QUIC and authenticated streams.
- Store secrets outside the repository and restrict access to the node key and memory master key.
- Add namespace-level authorization; the current shared token authenticates the whole invitation network.
- Add request-size, rate, concurrency and egress limits at a reverse proxy and in the worker sandbox.
- Run inference workers with a dedicated low-privilege account and model-specific license allowlists.
- Back up and rotation-test encryption keys before storing long-lived user memory.
- Review the data-retention, deletion, personal-information and model-license obligations for your jurisdiction.

## Reporting

Do not open a public issue containing credentials, private memory content, model keys or exploitable details. Contact the repository owner through GitHub security reporting instead.

