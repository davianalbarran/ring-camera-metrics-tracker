# Event-Driven Metrics Ingestion Service Requirements

## 1. Problem Statement
Design a system that ingests high-volume events from clients, buffers them reliably, and makes them available for both real-time counters and durable storage for downstream analytics.
The system should be horizontally scalable, resilient to partial failures, and suitable as the ingestion layer of a larger analytics platform.

## 2. Goals and Non-Goals

### Goals
- Accept events via a simple HTTP API
- Decouple ingestion from storage and processing
- Support near-real-time metrics
- Persist raw events durably for replay and analytics
- Demonstrate production-style service patterns

### Non-Goals
- Exactly-once delivery semantics end-to-end
- Complex user authentication / authorization
- Multi-region replication
- Strict real-time SLAs (sub-millisecond)

## 3. Assumptions & Constraints
- Events are append-only
- Event schema is known and versioned
- Moderate scale for a prototype: ~5k–20k events/sec
- Latency target is seconds, not milliseconds
- Kubernetes cluster is single-region
- Kafka is the system of record for ingestion

## 4. High-Level Architecture (Conceptual)
- Ingestion API (Go)
  - Stateless HTTP service
  - Produces events to Kafka
- Kafka
  - Durable buffer
  - Decouples producers from consumers
- Consumer Service (Go)
  - Reads from Kafka
  - Writes raw events to Postgres
  - Updates counters in Redis
- Postgres
  - Durable raw event storage
- Redis
  - Hot, low-latency metrics
- Kubernetes
  - Orchestration and scaling

## 5. Functional Requirements

### FR-1: Event Ingestion API
- System shall interface with Ring API to ingest events
- Events must include:
  - Event type
  - Timestamp
  - Source identifier
  - Arbitrary metadata payload
- API should return success once event is accepted into Kafka

### FR-2: Event Validation
- Ingestion service shall validate:
  - Required fields
  - Schema version
  - Payload size limits
- Invalid events must be rejected with clear error responses

### FR-3: Event Buffering
- Accepted events must be written to Kafka
- Kafka topics must be partitioned to support horizontal scaling
- Ordering must be preserved per partition key

### FR-4: Event Consumption
- A consumer service shall read events from Kafka
- Consumer shall support restart and replay from offsets

### FR-5: Durable Storage
- Raw events shall be persisted to Postgres
- Storage schema must support:
  - Time-based queries
  - Event type filtering

### FR-6: Real-Time Metrics
- System shall maintain counters such as:
  - Events per minute
  - Events per type
- Counters shall be stored in Redis
- Metrics should be queryable via a simple API

### FR-7: Failure Handling
- If Postgres is unavailable:
  - Kafka consumption must pause or retry
- If Redis is unavailable:
  - Event ingestion must continue
  - Metrics may be temporarily degraded

## 6. Non-Functional Requirements

### NFR-1: Scalability
- Ingestion service must scale horizontally
- Kafka partitions must support increased throughput
- Consumers must scale independently

### NFR-2: Reliability
- System should tolerate:
  - Pod restarts
  - Temporary datastore outages
- No event loss once accepted into Kafka

### NFR-3: Performance
- Ingestion API p95 latency < 100ms under normal load
- Kafka write latency should not block request threads excessively

### NFR-4: Observability
- Services must expose:
  - Health checks
  - Basic metrics (request rate, error rate)
  - Structured logs
  - Kafka consumer lag must be observable

### NFR-5: Deployability
- All components must be containerized
- System must be deployable via Kubernetes manifests
- Configuration should be externalized (env or config maps)

### NFR-6: Maintainability
- Clear service boundaries
- Strong typing for event schemas
- Minimal coupling between components

## 7. Open Design Questions (Interview Discussion)
- How many Kafka partitions?
- At-least-once vs at-most-once semantics?
- Backpressure strategy if consumers lag?
- Schema evolution approach?
- Redis eviction policies?