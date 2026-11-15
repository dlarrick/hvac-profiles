# Contributing to HVAC Profiles

Thank you for helping expand the open HVAC equipment profile database!

## What Makes a Good Profile

1. **Authoritative Source Data:** Prefer manufacturer engineering/submittal tables, NEEP Cold Climate Air Source Heat Pump (ccASHP) listings, or AHRI certificates over estimates.
2. **File Naming & Organization:**
   * Place profiles under `producers/<manufacturer_slug>/<model_slug>.json` (lowercase, underscores or hyphens, no spaces).
   * Example: `producers/mitsubishi/mxz_3c24nahz4.json`.
3. **Generalized Curves:** Capacity is configured per installation in `hvac-fusion`; profiles capture normalized performance curves (e.g., COP and capacity derate vs. outdoor temperature, condensing return-water efficiency curves, etc.).
4. **Validation:** All pull requests are validated by CI against the repository's JSON Schema and sanity checks. You do **not** need to generate or edit `index.json` — CI generates it automatically on merge.

## Licensing

By submitting a pull request to this repository, you agree that your contributions are licensed under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** license (see [LICENSE](LICENSE)).
