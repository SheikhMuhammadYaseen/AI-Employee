---
name: generate-architecture
description: Generate or update the Architecture.md documentation in the vault.
---

# Generate Architecture Documentation

Generate or update the Architecture.md documentation in the vault.

## Instructions

1. Analyze the current project structure and components.
2. Generate a comprehensive architecture document covering:
   - Component diagram (Perception → Reasoning → Action)
   - MCP server topology (3 servers: accounting, social, communications)
   - Data flow diagrams
   - Integration points (Odoo, social APIs, email)
   - Audit logging flow
   - Ralph Wiggum loop architecture

## Output

Write to `vault/Architecture.md` with sections:
- System Overview
- Component Architecture
- MCP Server Topology
- Data Flows
- Integration Points
- Security Model
- Error Recovery Strategy

## Usage

Review and update architecture documentation to reflect current system state after any significant changes.
