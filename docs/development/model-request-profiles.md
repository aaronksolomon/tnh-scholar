---
title: "Model Request Profiles"
description: "Maintain model reasoning and sampling compatibility through the provider registry."
owner: ""
author: "Codex"
status: current
created: "2026-09-19"
---
# Model Request Profiles

The OpenAI adapter reads `ModelInfo.request_profile` from the same registry used
for pricing and output limits. Model names and reasoning levels are data; the
adapter does not infer capabilities from model-name prefixes. Exact model keys
and explicit registry aliases are supported. Register snapshot names explicitly.

## Updating a model

Edit `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`, or supply
a provider registry under `registries/providers/openai.jsonc` in the workspace
or user configuration root. Provider files are selected in workspace, user,
then bundled order; a higher-precedence file replaces the entire provider file.
Do not expect new bundled models to appear through a stale local provider file.

Add the model's identity, limits, capabilities, pricing, and request profile:

```json
"request_profile": {
  "reasoning_efforts": ["low", "medium", "high", "xhigh", "max"],
  "default_reasoning_effort": null,
  "temperature": "never"
}
```

- `reasoning_efforts` lists literal API values. New levels require only a registry
  edit. Unknown levels fail before provider dispatch and show supported values.
- `default_reasoning_effort` is an application default, used when neither CLI nor
  configuration selects an effort. It must belong to `reasoning_efforts`.
  Null omits the field and uses the provider default.
- `temperature` accepts `always`, `never`, or `without_reasoning`. The last mode
  permits temperature for literal `none`. Set `temperature_without_effort: true`
  only when the provider also accepts temperature with the reasoning field omitted.
- Profiles without reasoning support use an empty effort list. Older registries
  without profiles default to no explicit reasoning and temperature allowed;
  reasoning models in such files must be updated with an explicit profile.
- `auto` is reserved for omitting the API field. `none` and `max` are literal
  provider values. The implementation never silently downgrades an effort.

Existing models can have their complete `request_profile` replaced in
`registries/overrides/openai.jsonc`, alongside existing pricing overrides:

```json
{
  "schema_version": "1.0",
  "provider": "openai",
  "models": {
    "gpt-6-astra": {
      "request_profile": {
        "reasoning_efforts": ["low", "medium", "high", "xhigh", "max"],
        "default_reasoning_effort": "high",
        "temperature": "never"
      }
    }
  }
}
```

Overrides modify existing models; new models belong in the provider file.
Restart the process after changing registries because the loader caches them.
Validate with `tests/gen_ai_service/test_model_request_profiles.py` and the
provider, registry, safety, and CLI suites. The regression suite includes a new
model with a new effort defined solely in a temporary registry.

## Astra and pricing

Astra's bundled profile targets the existing Chat Completions text/structured
output transport. Its function-calling flag is false here because Astra tool
calling requires Responses. New endpoints or new parameter shapes still require
transport implementation; registry entries cannot create those capabilities.

Prices are dollars per **1K** tokens. Astra standard rates are 0.01 input,
0.05 output, 0.001 cached input, and 0.0125 cache-write input. Before dispatch,
the estimator conservatively uses the larger input/cache-write rate. Above
272,000 input tokens, `long_context` multiplies all input/cache rates by 2 and
output rates by 1.5. This covers an individual request, not retry totals or an
exact invoice. Other models' pricing was not refreshed in this change; the
registry's overall freshness date is intentionally unchanged.

Sources checked September 19, 2026:

- [Astra model specification](https://developers.openai.com/api/docs/models/gpt-6-astra)
- [Astra migration guidance](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-5.4 parameter compatibility](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4)
- [GPT-5.5 reasoning levels](https://developers.openai.com/api/docs/models/gpt-5.5)

See [tnh-gen CLI reference](/cli-reference/tnh-gen.md) for reasoning precedence
and the changed `max`, `none`, and `auto` semantics.
