# Axaliai repository integration

This repository is the current integration hub for the Axaliai/Unity AI application layer.

## Connected repositories

| Repository | Integration role |
|---|---|
| `axali-sys/Unity-AI-Voice-Interface` | Mobile AI / voice core |
| `axali-sys/binance-spot-api-docs` | Market API reference |
| `axali-sys/zeek` | Network/security tooling reference |
| `axali-sys/openclaw-mission-control` | Mission-control tooling |

The canonical machine-readable registry is `config/axaliai-repositories.json`.

## Integration rule

Repositories are linked by role and source URL rather than copied into one codebase. This keeps each project independently versioned while allowing the Axaliai application layer to reference the appropriate component.

## Flutter/mobile direction

The eventual Flutter Android/iOS application should consume this registry through a small repository/service layer. Application code should not embed Git credentials or private tokens.
