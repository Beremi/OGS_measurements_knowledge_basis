# Thermal Expansivity Parameter Audit

This audit isolates the suspicious `CTE` parameter in the recovered OGS model.

## Current Finding

- Status: `blocked_confirm_cte_value`
- XML parameter: `CTE = 1254.74`
- Bound OGS property: `Solid:thermal_expansivity:Parameter`
- Expected unit from the OGS property role: `1/K`
- XML comment: `coefficient of linear thermal_expansivity [J/kgK]`
- Solid heat capacity in the same file: `c_p_s = 1254.74`
- `CTE` equals `c_p_s`: True

The value is not plausible as a solid thermal expansivity.  It appears to be a copied heat-capacity number or a unit/provenance error, because the same numeric value is used for `c_p_s`.

## Reference Scale

- Garitte et al. HE-D modelling table range: 1.00e-05 to 2.60e-05 1/K.
- Gens et al. thermal-loading analysis adopted value: 1.40e-05 1/K.
- XML `CTE` / high end of HE-D range: 4.826e+07.
- XML `CTE` / Gens et al. adopted value: 8.962e+07.

## Release Gate

Do not release or physically interpret CTE until Gesa/BGR confirms whether the XML value should be near 1e-5 1/K, a different value, or inactive in the intended run.

## Audit Rows

| Item | XML name | XML value | Expected unit | Plausibility | Gate |
| --- | --- | ---: | --- | --- | --- |
| solid thermal expansivity parameter | `CTE` | 1254.74 | 1/K | `implausible_by_units_and_magnitude` | `blocked_confirm_value_with_Gesa_or_BGR` |
| solid specific heat capacity comparison | `c_p_s` | 1254.74 | J/(kg K) | `plausible_as_heat_capacity_not_as_expansivity` | `fixed_thermal_constant_not_fitted` |

## Source Basis

- OGS binding: `04_media_TRM.xml` solid `thermal_expansivity` property points to `CTE`.
- XML value/comment: `03_parameters_TRM.xml` defines `CTE = 1254.74` with a heat-capacity-like comment.
- Literature scale: Garitte2017 PDF p. 12; Gens2017 PDF p. 14.
