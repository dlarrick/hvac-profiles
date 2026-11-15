# HVAC Profiles

Community-maintained equipment performance profiles for [`hvac-crossover`](https://github.com/dlarrick/hvac-crossover) and [`hvac-fusion`](https://github.com/dlarrick/hvac-fusion).

## Overview

This repository decouples real-world HVAC equipment performance curves (heat pumps, mini-splits, modulating/condensing boilers, atmospheric boilers, furnaces, etc.) from the `hvac-crossover` Python library and the `hvac-fusion` Home Assistant integration.

* **Pull Requests** are automatically validated against the profile JSON Schema and physical sanity checks.
* **Merges to `main`** publish a compact index (`index.json`) and validated profile files to GitHub Pages for runtime consumption.
* **Generic fallback profiles** remain bundled inside `hvac-crossover` for offline resilience and unit testing.

## Directory Layout

```text
hvac-profiles/
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/               # Schema validation & GitHub Pages publishing (upcoming)
├── producers/                   # Equipment profiles organized by manufacturer slug
│   └── <manufacturer>/
│       └── <model>.json
├── schema/                      # JSON Schema definitions (upcoming)
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Contributing

Contributions of new manufacturer/model profiles and corrections to existing curves are welcome!

> [!IMPORTANT]
> **[CONTRIBUTING.md](CONTRIBUTING.md) is not just boilerplate** — it explains where to source data (NEEP ccASHP, AHRI, engineering submittals), how to avoid common pitfalls like mixing up **full-load vs. part-load COP**, and how to normalize `capacity_percentage`. Please read it before creating your first profile.

## License

Equipment profile data in this repository is licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**. See [LICENSE](LICENSE) for details.
