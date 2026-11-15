# Contributing to HVAC Profiles

Thank you for helping expand the open HVAC equipment profile database! This guide covers the practical details needed to build an accurate profile—especially for inverter heat pumps, where datasheet numbers are easy to misread.

---

## 1. File Naming & Structure

* Place each profile at `producers/<manufacturer_slug>/<model_slug>.json`.
* Use lowercase letters, digits, underscores, or hyphens (`^[a-z0-9][a-z0-9_-]*$`).
  * Example: `producers/mitsubishi/mxz_xcxxnahz2.json`
* **No manual index updates:** `index.json` is generated automatically by CI on merge and is not tracked in git.
* **Keep profiles generalized:** Installation-specific details (`nominal_btu`, `primary_flow_gpm`, `has_outdoor_reset`) are configured per-home in `hvac-fusion` and are rejected by the schema.

---

## 2. Where to Find Authoritative Data

Prefer published test/engineering data over marketing brochures:

1. **NEEP Cold Climate Air Source Heat Pump (ccASHP) List:** Often the cleanest source for inverter heat pumps—it tabulates **Max** and **Min** capacity + COP at 47°F, 17°F, 5°F, and minimum operating temperature.
2. **Manufacturer Engineering Submittals / Extended Capacity Tables:** Look for heating capacity and COP/power input tables across outdoor temperatures. When tables vary by indoor return air temperature, use **70°F** (or **68°F** / 20°C).
3. **AHRI Certificates / Spec Sheets:** Reliable for boiler/furnace `rated_afue`, `turndown_ratio`, and baseline 47°F/17°F heat pump ratings.

Please cite your source (URL or document name) in the Pull Request description so reviewers can verify the numbers.

---

## 3. Building an `inverter_heat_pump` Profile

### Full-Load vs. Part-Load COP (Common Pitfall!)

`hvac-crossover` interpolates between `full_load_cop` and `part_load_cop` based on how hard the heat pump is working relative to its available capacity at the current outdoor temperature. Mixing these two up—for example, putting rated/part-load COP into `full_load_cop`—will skew the economic crossover calculation.

* **`full_load_cop` (Required):** COP when the compressor is running at **maximum capacity** for that outdoor temperature.
  * In NEEP ccASHP tables, this corresponds to the **Max** capacity row.
  * In engineering submittals, check whether the table is for **Maximum** vs. **Rated** capacity (rated 47°F heating is often a part-load point on variable-speed inverters!).
  * `full_load_cop` is typically *lower* than `part_load_cop` at mild temperatures (47°F) because the compressor is working harder against the same coil surface area.
* **`part_load_cop` (Optional, Strongly Encouraged):** COP when the inverter modulates down to a **minimum or intermediate steady-state load**.
  * In NEEP ccASHP tables, this corresponds to the **Min** (or intermediate) capacity row.
  * Typically *higher* than `full_load_cop` at 47°F and 17°F.
  * If a manufacturer only publishes a single curve at maximum capacity, omit `part_load_cop` rather than duplicating `full_load_cop`.

### `capacity_percentage`

`capacity_percentage` represents the heat pump's **maximum available heating capacity** at each outdoor temperature as a percentage of its **47°F rated/nominal capacity**:

$$\text{capacity\_percentage}(T) = \frac{\text{Max Heating BTU/hr at } T}{\text{Rated Heating BTU/hr at } 47^\circ\text{F}} \times 100$$

* At `47`°F this is normally `100.0` (some inverter units can boost above `100.0` at 47°F; the schema allows up to `150.0`).
* Cold-climate ("hyper-heat") units often hold `100.0` down to `17`°F or `5`°F before derating at `-13`°F; standard units typically derate smoothly below `47`°F.
* Use integer or decimal outdoor temperatures in **°F** as string keys (e.g., `"47"`, `"17"`, `"5"`, `"-13"`).

### `min_operational_temp_f`

* Lowest outdoor temperature (°F) at which the unit is rated to operate in heating mode.
* Any temperature keys in `full_load_cop` and `capacity_percentage` must be $\ge$ `min_operational_temp_f`.

---

## 4. Building Boiler & Furnace Profiles

Supported `producer_type` values: `modulating_boiler`, `atmospheric_boiler`, `steam_boiler`, `furnace`.

* **`rated_afue`:** Express as a decimal between `0` and `1.0` (e.g., `0.95` for 95% AFUE, not `95`).
* **`fuel_type`:** One of `"natural_gas"`, `"propane"`, or `"oil"`.
* **`turndown_ratio` (`modulating_boiler` only):** Ratio of max input to min input (e.g., `10.0` for a 10:1 modulating boiler).

---

## 5. Validating Locally

Every PR is checked against [schema/v1/producer.schema.json](schema/v1/producer.schema.json) and physical sanity rules. You can run the same checks locally before pushing:

```bash
pip install -r requirements-ci.txt
python scripts/validate_profiles.py
```

Or using `pre-commit` (which also auto-formats JSON with 2-space indentation while preserving key order):

```bash
pre-commit install
pre-commit run --all-files
```

---

## 6. Licensing

By submitting a pull request to this repository, you agree that your contributions are licensed under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** license (see [LICENSE](LICENSE)).
