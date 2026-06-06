# Plugins

Plugins are registry entries that extend strategy, notifier, or operator
integration surfaces without weakening the core runtime boundary.

## Usage

```bash
uv run nfi-engine plugins list --config examples/futures-paper.yaml
uv run nfi-engine plugins inspect --group strategy --name adapter-smoke-strategy
```

The registry validates configured plugin roots and rejects disabled, duplicate,
or incompatible roots before runtime use.

## Boundaries

- Plugin metadata is parsed at config/preflight time.
- Runtime code receives typed plugin descriptors.
- Strategy execution still passes through the sandbox policy.
- A plugin cannot bypass circuit breakers, read-only mode, CSRF, or backup rules.

## Limitations

M1 provides the contract and CLI inspection path. It does not provide a public
plugin marketplace or remote plugin installer.
