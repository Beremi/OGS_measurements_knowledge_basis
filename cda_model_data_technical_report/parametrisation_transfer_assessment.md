# Transfer assessment: TSX/DAHMC parameterisation ideas for the CD-A OGS inversion

Date: 2026-06-01

Source reviewed: `Subchain_DAHMC_paper.pdf`, "Delayed acceptance sampling with Hamiltonian proposal subchains for random field materials inference".

## Executive assessment

Several ideas from the TSX/DAHMC report are transferable to the CD-A work, but not as a direct copy.

The useful transfer is the *parameterisation*, not primarily the DAHMC sampler:

- sample or optimise in standardised latent coordinates;
- reconstruct positive material fields through logarithmic transforms;
- use reduced-rank spatial bases rather than independent cell-wise parameters;
- choose basis dimension using both prior variance and likelihood sensitivity;
- separate global smooth fields, local test-supported corrections, scalar calibration parameters, and boundary/observation-model parameters into blocks.

For CD-A, the best near-term parameterisation is not a single smooth KL field.  The direct permeability data are local, support-conflicted, and concentrated around BCD-A32/A33.  A pure low-rank smooth KL field would likely underfit these local features or smear them into physically implausible regions.  The better transfer is a **hybrid latent field**:

\[
\log_{10} k_{\mathrm{mag}}(x)
= m_k(x)
+ B_{\mathrm{global}}(x) z_{\mathrm{global}}
+ B_{\mathrm{EDZ}}(x) z_{\mathrm{EDZ}}
+ B_{\mathrm{local}}(x) z_{\mathrm{local}},
\qquad z \sim \mathcal N(0,I).
\]

The current fixed tensor angle and anisotropy can then reconstruct the full positive-definite permeability tensor.  This preserves the successful CD-A local-basis behaviour while giving a cleaner Bayesian/prior-coordinate structure for optimisation and later MCMC.

## What the TSX/DAHMC report actually did

The TSX benchmark used a much simpler inverse problem:

- two-dimensional Biot poroelasticity;
- four pressure time series sampled at 18 times, giving 72 observations;
- uncertain hydraulic conductivity, porosity, drained bulk modulus, shear modulus, and grain bulk modulus;
- hydraulic conductivity and porosity represented as nonstationary Gaussian random fields;
- random fields approximated with truncated Karhunen-Loeve expansions;
- scalar mechanical parameters represented by a small number of inner/outer values;
- sampling in "inner coordinates": KL coefficients plus centred/scaled scalar parameters.

The core field parameterisation was:

\[
g_M(x) = \sum_{m=1}^{M} \xi_m \sqrt{\lambda_m}\,v_m(x),
\qquad \xi_m \sim \mathcal N(0,1),
\]

followed by logarithmic positive transforms:

\[
K(x)=10^{\mathrm{GRF}_K(x)-13},
\qquad
\phi(x)=10^{\mathrm{GRF}_{\phi}(x)-2.5}.
\]

The covariance was nonstationary: correlation length and marginal standard deviation varied with distance from the tunnel.  Truncation dimension was chosen in two steps:

1. retain enough modes to capture a target fraction of prior variance;
2. perturb posterior-relevant parameter vectors and check whether the likelihood response stabilises as more modes are retained.

This led to 40 KL modes for hydraulic conductivity and 40 KL modes for porosity, plus 5 scalar mechanical parameters.

## Directly transferable ideas

### 1. Whitened prior coordinates

Transferability: high.

CD-A should use standard normal latent variables for any stochastic field:

\[
z_i \sim \mathcal N(0,1),
\qquad
\log_{10} k(x)=m_k(x)+\sum_i z_i b_i(x).
\]

This is useful for deterministic inversion, ensemble exploration, and future MCMC.  Optimisation in raw cell values or raw permeability values is badly scaled.  Optimisation in \(z\)-coordinates gives a clean prior penalty:

\[
\Phi_{\mathrm{prior}}(z)=\frac12 z^\top z.
\]

For CD-A this should replace the informal idea of "cell values as parameters" with a reproducible latent-to-field map.

### 2. Logarithmic parameterisation of permeability

Transferability: already partly used, should be formalised.

The CD-A active material is intrinsic permeability.  It is positive and spans many orders of magnitude, so \(\log_{10} k\) is the correct inversion variable.  The TSX approach confirms that posterior summaries should also be reported in log space.

For CD-A:

- invert \(\log_{10} k_{\mathrm{mag}}\), not \(k\);
- reconstruct the tensor from magnitude, fixed anisotropy ratio, and fixed bedding angle;
- keep the tensor positive definite by construction;
- report maps of posterior/ensemble mean and standard deviation of \(\log_{10} k_{\mathrm{mag}}\).

### 3. Reduced-rank spatial bases

Transferability: high, but only with a hybrid basis.

The KL idea is useful because it turns a large mesh field into a moderate number of physically correlated parameters.  However, CD-A should not use one smooth global KL basis as the whole parameterisation.  The direct pulse tests are local interval constraints and contain same-support conflicts.  A global smooth basis would either smooth them away or create long-range artefacts.

Recommended CD-A structure:

- **global smooth component** for broad background variability;
- **EDZ/niche component** with shorter length scale near the excavation and support zones;
- **local pulse-test component** around BCD-A32/A33 support cells, similar to the current local-basis field;
- optional **fault/fracture/structural component** only after structural support is accepted.

This captures the TSX benefit while respecting the CD-A data geometry.

### 4. Nonstationary covariance

Transferability: high, with anisotropic modification.

The TSX covariance made correlation length and variance depend on distance from the tunnel.  CD-A should do the same, but with bedding/EDZ anisotropy:

- shorter correlation length near the niche wall and EDZ;
- longer correlation length in intact rock;
- larger prior variance in damaged/support-conflicted zones;
- anisotropic correlation aligned with the \(144^\circ\) bedding-informed tensor direction;
- optional separate open/closed niche distance fields if both become active.

This is more defensible than a stationary Matérn/Gaussian prior over the whole OGS mesh.

### 5. Likelihood-informed truncation

Transferability: very high.

The TSX report did not choose 40 modes only from prior variance; it also checked likelihood sensitivity.  CD-A needs this even more because the streams have different spatial support and semantic reliability.

For each candidate basis dimension \(M\), test:

- direct permeability objective response;
- NMR raw and NMR anomaly response separately;
- ERT diagnostic response if accepted;
- Taupe/TDR trend response if accepted;
- regularity/roughness of the reconstructed field.

The practical rule should be:

> increase \(M\) until adding modes changes the relevant objective components only marginally, unless added modes are needed to represent known local support effects.

This should be done per block, not once globally.

### 6. Block parameterisation

Transferability: high.

The TSX paper separated KL field coefficients from scalar mechanical parameters.  CD-A should use explicit parameter blocks:

- \(z_k\): log-permeability magnitude field coefficients;
- \(z_{\mathrm{local}}\): local pulse-test correction coefficients;
- \(z_{\mathrm{NMR,bias}}\): optional NMR label/campaign bias or bound-water offset parameters;
- \(z_{\mathrm{ERT,cal}}\): ERT calibration/covariance parameters, only after ERT gates close;
- \(z_{\mathrm{Taupe,cal}}\): Taupe/TDR calibration or trend-scale parameters, only after unit/calibration gates close;
- \(z_{\mathrm{RH,bc}}\): low-dimensional open-niche boundary pressure curve correction, only after RH provenance is settled;
- \(z_{\mathrm{mech}}\): elasticity/swelling/HM parameters, only after numeric HM exports exist.

This block structure directly addresses CD-A confounding between permeability, boundary pressure, retention, NMR semantics, and geophysical calibration.

### 7. pCN and prior-respecting proposals for later MCMC

Transferability: high for uncertainty quantification, lower for the immediate deterministic fit.

If CD-A moves to MCMC, pCN in whitened coordinates is a good robust baseline because it respects the Gaussian prior:

\[
z'=\sqrt{1-\beta^2}\,z+\beta\eta,\qquad \eta\sim\mathcal N(0,I).
\]

This is more stable than random-walk proposals on raw permeability cells.  It is also compatible with delayed acceptance if a cheap surrogate or coarse OGS run exists.

## Conditionally transferable ideas

### 1. Porosity as a random field

Transferability: low now, possible later.

The TSX case inverted porosity because pressure observations and the simpler model could support it.  CD-A should not yet promote porosity to a random field.

Reasons:

- current porosity is fixed at \(n=0.105\);
- NMR measures total hydrogen-bearing water, not just mobile \(nS_\ell\);
- ERT/Taupe calibration is not yet accepted;
- porosity, saturation, retention, and bound/interlayer water are strongly confounded.

If porosity is later released, use a bounded/logit or tightly constrained latent field, not an unconstrained lognormal field.  It should enter only after NMR residual policy and geophysical calibration are settled.

### 2. Mechanical scalar/EDZ parameterisation

Transferability: later, not now.

The TSX inner/outer drained-bulk and shear-modulus parameters are a good template for CD-A HM calibration, but CD-A currently lacks machine-readable HM time series and uncertainty metadata.

Recommended later form:

\[
E(x),\ \mu(x),\ \alpha_{\mathrm{sw}}(x)
= \text{inner EDZ value} \rightarrow \text{outer intact value}
\]

with a smooth distance-to-niche transition.  Do not activate this before extensometer, levelling, crackmeter, laser-scan, or convergence data are numerically available.

### 3. Neural-network surrogate with delayed acceptance

Transferability: algorithmically possible, but not the immediate bottleneck.

The TSX/DAHMC sampler uses a neural-network surrogate, Hamiltonian subchains, and delayed-acceptance correction.  For CD-A this is attractive only after the objective is stable.

Immediate risks:

- OGS/TRM is nonlinear and more expensive;
- gradients of the exact model are not available;
- surrogate gradients can be misleading outside the trained posterior region;
- adaptive surrogate MCMC requires fixed snapshots inside transitions and diminishing adaptation;
- if the observation operator is still changing, sampler correctness is a secondary issue.

Useful near-term role:

- train surrogates for diagnostic screening of candidate fields;
- use delayed acceptance only with exact OGS correction;
- freeze surrogate snapshots for production runs.

## Not directly transferable

### A single 40-mode KL field

The number 40 was justified for the TSX mesh, TSX covariance, and TSX observations.  It has no direct meaning for CD-A.  CD-A has different mesh geometry, measurement supports, and data conflicts.  CD-A should choose its own basis dimensions by block.

### Smooth porosity/permeability-only calibration

TSX had pressure time series as the main observable.  CD-A combines direct permeability, NMR, ERT, Taupe/TDR, RH boundary information, and future HM streams.  A parameterisation that works for one pressure-likelihood problem may hide observation-operator errors in CD-A.

### Treating all observations as one Gaussian vector

CD-A needs stream-specific likelihoods and gates.  Direct permeability, NMR, ERT, Taupe/TDR, RH, and HM streams have different supports, covariances, and readiness levels.  Combining them into one undifferentiated Gaussian vector would be unsafe.

## Recommended CD-A implementation path

### Stage 1: formalise the current active field in latent coordinates

Keep the current active objective: direct permeability plus NMR, with gated diagnostics.  Replace ad hoc field updates by a documented latent map:

\[
\log_{10} k_{\mathrm{mag}}(x)
=m_k(x)+B_{\mathrm{local}}(x)z_{\mathrm{local}}
\]

or

\[
\log_{10} k_{\mathrm{mag}}(x)
=m_k(x)+B_{\mathrm{global}}(x)z_{\mathrm{global}}+B_{\mathrm{local}}(x)z_{\mathrm{local}}.
\]

Use \(z^\top z/2\) as a prior regularisation term.  Keep porosity, tensor angle, tensor ratio, retention, and boundary pressure fixed.

### Stage 2: build a nonstationary anisotropic basis

Construct covariance/basis functions on OGS cell centroids:

- distance to niche boundary;
- optional distance to mapped EDZ/support zones;
- bedding-aligned anisotropy at \(144^\circ\);
- short length scales near the niche and pulse-test supports;
- longer length scales away from the excavation.

Use either KL eigenmodes of the covariance matrix or deterministic radial/local basis functions if the covariance eigenproblem is too costly.

### Stage 3: choose truncation by likelihood sensitivity

For candidate dimensions per block, perturb the incumbent field in whitened coordinates and evaluate:

- direct permeability residual;
- NMR residual under raw and anomaly policies;
- ERT and Taupe/TDR diagnostics only if accepted or explicitly scenario-tested.

This gives a CD-A-specific equivalent of the TSX likelihood-informed truncation plot.

### Stage 4: add observation-model parameters only after gates close

Do not use permeability modes to compensate for:

- NMR bound-water offsets;
- ERT calibration/covariance errors;
- Taupe unit/calibration ambiguity;
- RH boundary-curve provenance;
- missing HM support/sign conventions.

Each should become its own small parameter block only after its data gate is closed.

### Stage 5: use prior-respecting MCMC only after the objective is stable

For uncertainty quantification:

- start with pCN in whitened field coordinates;
- use block proposals for local/global field blocks;
- consider delayed acceptance with a frozen surrogate or coarse objective;
- only then consider HMC/DAHMC with surrogate gradients.

## Bottom line

The TSX parameterisation ideas are strongly transferable if interpreted as a **latent-coordinate, log-field, reduced-rank, nonstationary prior framework**.

They are not transferable as:

- "use 40 KL modes";
- "also invert porosity now";
- "replace current local CD-A field with one smooth global KL field";
- "use neural-network HMC before the CD-A likelihood is final".

The most defensible CD-A next step is a hybrid parameterisation:

\[
\boxed{
\log_{10} k_{\mathrm{mag}}(x)
=m_k(x)
+B_{\mathrm{global}}(x)z_{\mathrm{global}}
+B_{\mathrm{EDZ}}(x)z_{\mathrm{EDZ}}
+B_{\mathrm{local}}(x)z_{\mathrm{local}},
\quad z\sim\mathcal N(0,I)
}
\]

with fixed porosity, fixed tensor orientation/ratio, and stream-specific observation gates.  This transfers the useful TSX idea while respecting the much harder CD-A measurement structure.
