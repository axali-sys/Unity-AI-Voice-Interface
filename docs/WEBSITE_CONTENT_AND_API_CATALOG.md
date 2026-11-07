# Axaliai website content and service catalogue

## Public positioning
Axaliai is the umbrella identity for a general AI infrastructure ecosystem. It is not the IDEAS marketplace. Product identities remain distinct and can consume shared infrastructure through documented interfaces.

## Architecture catalogue
| Layer | Responsibility | Public status wording |
|---|---|---|
| AI Core | Intelligence and model access | Architecture direction; integrations vary by environment |
| Omni | Workflow orchestration | Planned/under development unless verified per deployment |
| Parallel Intelligence | Multi-system collaboration and comparison | Do not imply consensus without independent evidence |
| XParallel | Execution and interoperability infrastructure | Existing repository implementation; live status must be tested |
| OmniMemory / Knowledge Genome | Knowledge records, provenance and retrieval | Roadmap capability; verify each component before claiming operational |
| Engineering Fabric | Build, repair and developer tooling | Product direction; distinguish prototypes from released services |
| Security and identity | Authorization, secrets, audit and workspace boundaries | Publish verified controls and explicit limitations |

## Product identity boundaries
- Axaliai: umbrella infrastructure ecosystem and public website.
- ƎllE: assistant product identity.
- NexAI: separate independent AI assistant product.
- XParallel: execution and interoperability infrastructure.
- IDEAS: separate global ideas marketplace; not part of Axaliai website navigation as a product offering.

## API publication rules
1. Do not publish an endpoint as available until the exact route, method, authentication model, request/response schema and environment are verified.
2. Never publish credentials, bearer tokens, private service URLs or secret environment variables.
3. Mark examples as illustrative and never present static examples as live responses.
4. Include rate limits, data handling, error semantics and versioning before general release.
5. A successful build or unit test is not proof of live production availability.

## Contact and launch checklist
- Replace the placeholder contact email with a verified inbox.
- Confirm legal entity, privacy policy, terms, data handling and cookie requirements.
- Confirm Squarespace DNS ownership and Vercel preview/production separation before domain connection.
- Run accessibility, mobile, link, metadata, dependency and build checks.
- Obtain explicit approval before DNS edits, paid resources, production deploy or merging to main.
