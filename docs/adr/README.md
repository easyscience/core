# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the EasyScience corelib project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences. ADRs help teams:

- Understand why certain design decisions were made
- Onboard new team members
- Evaluate whether past decisions still make sense
- Avoid repeating discussions about already-decided issues

## ADR Format

Each ADR follows this structure:

- **Title**: ADR number and descriptive title
- **Status**: Proposed, Accepted, Deprecated, or Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision or change?
- **Decision**: What is the change that we're proposing and/or doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?
- **Alternatives Considered**: What other options were evaluated?
- **Implementation Details**: Technical details of the implementation
- **References**: Links to related issues, PRs, or documentation
- **Decision Date**: When this decision was made

## ADR Lifecycle

1. **Proposed**: Initial draft, under discussion
2. **Accepted**: Decision has been approved and implemented
3. **Deprecated**: No longer relevant but kept for historical reference
4. **Superseded**: Replaced by a newer ADR (link to the new one)

## List of ADRs

- [ADR-0001](0001-model-collection-for-list-based-models.md) - ModelCollection for List-Based Model Management (Proposed)

## Creating a New ADR

When creating a new ADR:

1. Use the next available number (e.g., `0002-descriptive-title.md`)
2. Start with status "Proposed"
3. Include all relevant context and technical details
4. Link to related issues or pull requests
5. Update this README with the new ADR

## Further Reading

- [Architecture Decision Records (ADR) on GitHub](https://adr.github.io/)
- [Documenting Architecture Decisions by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
