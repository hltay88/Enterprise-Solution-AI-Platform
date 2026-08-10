# Agent Tools and Guardrails

Tools may include knowledge search, project retrieval, architecture lookup, BOM lookup, calculations, document generation and validation.

Controls: least privilege, read-only by default, explicit write authorization, schema validation, tenant isolation, audit tool calls, rate limits, timeouts/circuit breakers and prompt-injection defense.

Agents cannot silently modify approved RKM, architecture, BOM or documents.
