# NeuronMesh: Spatial and Metaverse Integration Boundary

[简体中文](../../神经元式去中心化大模型网络系统-元宇宙接入预留方案.md) | [English](metaverse-integration.en.md)

**Status:** Design baseline for future integration  
**English edition note:** This is an international collaboration translation/adaptation. The Chinese source remains authoritative when exact wording matters.

## 1. Decision

NeuronMesh reserves a spatial interface but does not implement a metaverse platform in the first release.

The durable core remains responsible for:

- virtual-role identity;
- memory scopes and retrieval;
- model and adapter versions;
- policy and action grants;
- training and audit history.

WebXR, OpenXR, Unity, Unreal or a proprietary world engine is responsible only for presentation, spatial input and world actions through a replaceable adapter.

This avoids coupling memory and inference to an engine SDK or a single headset ecosystem.

## 2. Layering

```text
Spatial client
  -> versioned Spatial Adapter
    -> ephemeral Space Session
      -> permission broker
        -> NeuronMesh role, memory and inference core
```

Required optional components:

- `Spatial Adapter Gateway`: translates WebXR/OpenXR/WebSocket/WebRTC/gRPC events;
- `Space Session Manager`: bounded, expiring frame-aware session state;
- `Avatar Intent Broker`: converts untrusted model proposals into authorized actions;
- `Scene Reference Registry`: maps world objects to authorized scope IDs;
- `Privacy Policy Adapter`: enforces sensor, bystander and retention rules.

## 3. Spatial session protocol

Every session declares:

- protocol and adapter versions;
- role and owner IDs;
- space and world IDs;
- frames and coordinate conventions;
- privacy mode;
- event deadlines and ordering constraints;
- allowed high-impact action categories;
- sensor retention policy;
- expiry and reconnect behavior.

### 3.1 Event envelope

An event includes:

```text
event_id
session_id
frame_id
source
event_type
monotonic_sequence
observed_at
deadline
payload_digest
payload
untrusted=true
```

Raw sensor data is ephemeral by default. Large media should be referenced by a scoped object ID rather than copied into control-plane logs.

### 3.2 Avatar intent

A model produces an intent, not an executed action:

```text
intent_id
role_id
action
target_scope
payload
confidence
requested_expiry
permission_token
```

The broker evaluates role policy, object scope, bystander privacy, current epoch and action risk before the world adapter may execute it.

## 4. Memory boundary

Spatial session state does not automatically become long-term memory.

Promotion requires:

1. explicit data class and purpose;
2. owner or policy grant;
3. evidence and provenance;
4. a retention period;
5. deletion scope;
6. removal of raw coordinates or media unless explicitly required.

By default:

- gaze, pose and raw camera frames remain ephemeral;
- microphone audio is not stored;
- world-object identifiers remain scoped;
- a summary may be proposed for memory but goes through the normal evidence gate;
- other participants' private data is not inferable into durable role memory.

## 5. Privacy modes

| Mode | Allowed data | Default use |
| --- | --- | --- |
| `local_only` | On-device sensor processing and local model | Private or high-risk interactions |
| `redacted_features` | Text, bounding boxes, transcript or embeddings with declared leakage | General spatial assistance |
| `encrypted_full_media` | Explicitly authorized encrypted media | Detailed visual/audio tasks |

Each mode names:

- who can decrypt or process data;
- whether data crosses a trust domain;
- maximum retention;
- whether derived features are considered personal data.

## 6. Transport

### 6.1 Real-time channel

Use WebRTC/WebTransport or another low-latency datagram/stream transport for:

- pose and controller events;
- VAD and interrupt signals;
- avatar gestures;
- bounded media features.

### 6.2 Control and durable channel

Use authenticated request streams for:

- memory writes and retrieval;
- role changes;
- model/Adapter versions;
- action grants;
- deletion and audit.

Real-time events must not become a second, unreviewed durable database.

## 7. Latency and ordering

- input events carry a deadline and monotonic sequence;
- expired events are dropped rather than executed late;
- generation begins only after the required frame/context is available;
- avatar actions are idempotent through `intent_id`;
- disconnect cannot replay already executed world actions;
- output from the model is untrusted until permission evaluation.

## 8. Permissions and immersive safety

High-impact actions include:

- spending resources;
- changing shared world state;
- recording/publishing media;
- contacting third parties;
- representing another person;
- physical-device actions.

They require a short-lived, scoped action grant. A role's general model access is not sufficient.

Bystanders have privacy expectations distinct from the role owner. The adapter must support:

- recording indicators;
- face/voice redaction;
- exclusion zones;
- retention controls;
- deletion requests;
- an audit of sensor-policy decisions.

## 9. Compatibility and acceptance

The initial desktop mock must demonstrate:

1. spatial event -> untrusted semantic input;
2. role and namespace permission checks;
3. memory retrieval within scope;
4. model output -> avatar intent;
5. high-impact action rejected without grant;
6. raw session coordinates absent from durable memory;
7. session expiry and safe disconnect.

Future WebXR/OpenXR adapters must pass engine-neutral conformance fixtures before claiming compatibility.

## 10. Phased implementation

### M0: protocol reservation

- freeze envelopes and version negotiation;
- define privacy and action-grant fields;
- add schema tests.

### M1: desktop simulator

- simulate headset/controller/scene events;
- demonstrate permission and memory boundaries;
- no real XR dependency.

### M2: WebXR adapter

- browser capability negotiation;
- WebXR session lifecycle;
- WebTransport or WebSocket fallback;
- reduced feature set on unsupported devices.

### M3: native OpenXR/engine adapter

- OpenXR runtime integration;
- Unity/Unreal plugin boundary;
- device capability declaration;
- retention and bystander controls.

### M4: cross-world interoperability

Only after identities, trust, deletion and cost models are stable:

- portable role manifests;
- scoped world references;
- cross-platform adapter conformance;
- federated spatial discovery.

## 11. Non-goals

- writing a game engine;
- making WebXR mandatory for non-spatial users;
- storing every sensor event;
- treating avatar appearance as role identity;
- executing an LLM-generated action without a permission broker;
- promising seamless operation on every headset.

## 12. External references

- [W3C WebXR Device API](https://www.w3.org/TR/webxr/)
- [W3C WebTransport](https://www.w3.org/TR/webtransport/)
- [Khronos OpenXR](https://registry.khronos.org/OpenXR/)
- [glTF](https://www.khronos.org/gltf/)
- [WebRTC](https://www.w3.org/TR/webrtc/)

See the Chinese source for the full design tables and patent-oriented wording.
