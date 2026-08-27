"""Curated scientific help shown by the portal for every released tool.

Equations are stored as LaTeX in ``tex`` and typeset by the vendored MathJax
bundle under ``static/vendor/mathjax``. Every equation also carries a ``plain``
spoken form used as the accessible label, so the content stays usable when
MathJax is unavailable or a screen reader is in use.
"""

from __future__ import annotations

from typing import Any

TOOL_HELP: dict[str, dict[str, Any]] = {
    "hydride-segmentation": {
        "purpose": "Identify hydride-like regions in micrographs, review the segmentation, and convert accepted regions into traceable morphology and orientation measurements.",
        "workflow": [
            "Calibrate and inspect the micrograph",
            "Choose a registered ML model or the conventional pipeline",
            "Segment and post-process connected features",
            "Review overlays and correct errors",
            "Export masks, measurements, provenance, and reports",
        ],
        "equations": [
            {
                "name": "Area fraction",
                "tex": r"f_{A} \;=\; \frac{A_{h}}{A_{\mathrm{ROI}}}",
                "plain": "f_A equals A_h divided by A_ROI",
                "meaning": "The segmented hydride area divided by the analyzed region area.",
                "where": [
                    (r"A_{h}", "total accepted hydride area in the region of interest"),
                    (r"A_{\mathrm{ROI}}", "area of the analyzed region of interest"),
                ],
            },
            {
                "name": "Equivalent circular diameter",
                "tex": r"d_{\mathrm{eq}} \;=\; 2\sqrt{\frac{A}{\pi}}",
                "plain": "d_eq equals 2 times the square root of A over pi",
                "meaning": "The diameter of a circle having the same segmented area as the feature.",
                "where": [
                    (r"A", "area of a single connected segmented feature"),
                ],
            },
            {
                "name": "Orientation (Kearns-type) factor",
                "tex": (
                    r"F_{n} \;=\; \frac{\displaystyle\sum_{i} A_{i}\cos^{2}\theta_{i}}"
                    r"{\displaystyle\sum_{i} A_{i}}"
                ),
                "plain": (
                    "F_n equals the sum over i of A_i times cosine squared theta_i, "
                    "divided by the sum over i of A_i"
                ),
                "meaning": "An area-weighted alignment measure; verify the configured reference direction before interpretation.",
                "where": [
                    (r"A_{i}", "area of segmented feature i"),
                    (
                        r"\theta_{i}",
                        "angle between feature i and the configured reference direction",
                    ),
                ],
            },
            {
                "name": "Aspect ratio",
                "tex": r"\mathrm{AR} \;=\; \frac{L_{\max}}{L_{\min}}",
                "plain": "AR equals L max divided by L min",
                "meaning": "Elongation of a fitted feature, used to separate platelet-like hydrides from equiaxed artefacts.",
                "where": [
                    (r"L_{\max}", "major axis length of the fitted ellipse"),
                    (r"L_{\min}", "minor axis length of the fitted ellipse"),
                ],
            },
        ],
        "inputs": [
            (
                "Image and calibration",
                "Pixel data establish the segmentation evidence; pixel size converts pixel measurements to physical units.",
            ),
            (
                "Model or method",
                "Selects learned inference or the auditable conventional threshold/morphology pipeline.",
            ),
            (
                "Thresholds and morphology controls",
                "Control foreground confidence, noise removal, gap closing, and connected-feature acceptance.",
            ),
            (
                "Reference direction",
                "Defines the zero angle used by orientation statistics and the orientation factor.",
            ),
        ],
        "limits": [
            "Segmentation is an estimate and must be visually reviewed.",
            "Pixel calibration and reference direction directly affect quantitative interpretation.",
            "Closely touching hydrides may merge; faint hydrides may be omitted by an aggressive threshold.",
        ],
        "external_help_suffix": "/help",
        "diagram": "help/hydride-segmentation-workflow.svg",
    },
    "pytex": {
        "purpose": "Analyze crystallographic orientation, texture, EBSD maps, diffraction geometry, TEM patterns, and phase transformations while keeping frames, symmetry, conventions, and provenance explicit.",
        "workflow": [
            "Import or construct phase and measurement data",
            "Normalize source conventions into PyTex canonical semantics",
            "Apply the selected texture, diffraction, EBSD, TEM, or OR algorithm",
            "Validate reductions and scientific assumptions",
            "Inspect explainable results and export figures or machine-readable contracts",
        ],
        "equations": [
            {
                "name": "Orientation mapping",
                "tex": r"\mathbf{v}_{s} \;=\; \mathbf{g}\,\mathbf{v}_{c}",
                "plain": "v_s equals g times v_c",
                "meaning": "The orientation maps crystal-frame vector components into the specimen frame.",
                "where": [
                    (r"\mathbf{g}", "orientation matrix, crystal frame to specimen frame"),
                    (r"\mathbf{v}_{c}", "vector components expressed in the crystal frame"),
                    (r"\mathbf{v}_{s}", "the same vector expressed in the specimen frame"),
                ],
            },
            {
                "name": "Bragg's law",
                "tex": r"2\,d_{hkl}\,\sin\theta_{B} \;=\; n\lambda",
                "plain": "2 d_hkl sine theta_B equals n lambda",
                "meaning": "Relates interplanar spacing, radiation wavelength, and the Bragg angle.",
                "where": [
                    (r"d_{hkl}", "interplanar spacing of the reflecting plane family"),
                    (r"\theta_{B}", "Bragg angle"),
                    (r"\lambda", "radiation wavelength"),
                    (r"n", "reflection order"),
                ],
            },
            {
                "name": "Misorientation",
                "tex": r"\Delta\mathbf{g} \;=\; \mathbf{g}_{2}\,\mathbf{g}_{1}^{-1}",
                "plain": "Delta g equals g_2 times g_1 inverse",
                "meaning": "The relative rotation, subsequently reduced under the declared crystal symmetries.",
                "where": [
                    (r"\mathbf{g}_{1},\,\mathbf{g}_{2}", "the two orientations being compared"),
                    (r"\Delta\mathbf{g}", "misorientation before symmetry reduction"),
                ],
            },
            {
                "name": "Interplanar spacing (hexagonal)",
                "tex": (
                    r"\frac{1}{d_{hkl}^{2}} \;=\; \frac{4}{3}\,"
                    r"\frac{h^{2}+hk+k^{2}}{a^{2}} \;+\; \frac{l^{2}}{c^{2}}"
                ),
                "plain": (
                    "one over d_hkl squared equals four thirds times the quantity "
                    "h squared plus h k plus k squared over a squared, plus l squared over c squared"
                ),
                "meaning": "The hexagonal metric used for zirconium-alloy plane spacings and diffraction predictions.",
                "where": [
                    (r"h,k,l", "Miller indices of the plane"),
                    (r"a,\,c", "hexagonal lattice parameters"),
                ],
            },
        ],
        "inputs": [
            (
                "Phase, lattice, and symmetry",
                "Fix the direct/reciprocal metric and allowed symmetry operations.",
            ),
            (
                "Reference frames and conventions",
                "Determine how vectors, orientations, maps, detectors, and laboratory axes are related.",
            ),
            (
                "Measurement geometry",
                "Carries wavelength, detector, calibration, scan, or microscope geometry required by the workflow.",
            ),
            (
                "Tolerance and reduction choices",
                "Control matching, family expansion, numerical acceptance, and representative selection.",
            ),
        ],
        "limits": [
            "Never compare orientations until mapping direction, angle convention, units, and symmetry are aligned.",
            "Kinematic diffraction predictions do not replace dynamical scattering where multiple scattering is important.",
            "Experimental surfaces are labeled as such and should not be reported as validated stable results.",
        ],
        "diagram": "help/pytex-workflow.svg",
    },
    "pdf-tools": {
        "purpose": "Preview, reorder, merge, split, and extract pages from any PDF — reports, scans, forms, presentations, invoices, manuscripts, or drawings — entirely inside the office intranet. Documents are processed in memory for the duration of your request and are never stored on the server or sent outside the office network.",
        "workflow": [
            "Upload one or more PDFs of any kind and validate type and size",
            "Read the page tree and preview the pages in the browser",
            "Select page ranges and arrange the document order",
            "Copy the selected page objects into a new document",
            "Stream the result back and discard every temporary byte",
        ],
        "equations": [
            {
                "name": "Page selection",
                "tex": (
                    r"P_{\text{out}} \;=\; \big\Vert_{\,j=1}^{\,m}\; "
                    r"P_{j}\bigl[a_{j} : b_{j}\bigr]"
                ),
                "plain": (
                    "P out equals the ordered concatenation, for j from 1 to m, "
                    "of the pages of document j from a_j to b_j"
                ),
                "meaning": "The output page sequence is the ordered concatenation of each selected inclusive page range.",
                "where": [
                    (r"P_{j}", "page list of the j-th input document"),
                    (r"a_{j},\,b_{j}", "first and last page of a selected one-based range"),
                    (r"\Vert", "ordered concatenation"),
                ],
            },
            {
                "name": "Output page count",
                "tex": r"N_{\text{out}} \;=\; \sum_{j=1}^{m}\,\bigl(b_{j}-a_{j}+1\bigr)",
                "plain": (
                    "N out equals the sum from j equals 1 to m of b_j minus a_j plus one"
                ),
                "meaning": "Every selected range is inclusive, so a 1-3 selection contributes three pages.",
                "where": [
                    (r"m", "number of selected ranges across all documents"),
                ],
            },
            {
                "name": "Displayed upload size",
                "tex": r"S_{\mathrm{MiB}} \;=\; \frac{S_{\text{bytes}}}{2^{20}}",
                "plain": "S in mebibytes equals S in bytes divided by two to the twentieth",
                "meaning": "Upload size is reported in binary mebibytes so the operational limit is unambiguous.",
                "where": [
                    (r"S_{\text{bytes}}", "raw uploaded size reported by the browser"),
                ],
            },
        ],
        "inputs": [
            (
                "Source files",
                "Any PDF is accepted regardless of subject matter — the tool reads only the page structure, never the meaning of your content.",
            ),
            (
                "Page ranges",
                "Use one-based user-facing ranges such as 1-3, 6; invalid or missing pages are rejected.",
            ),
            ("Document order", "Controls the exact concatenation sequence in a merge."),
            (
                "Export mode",
                "Selects a PDF result or raster page images where supported.",
            ),
        ],
        "limits": [
            "Reordering pages does not edit page content or repair a damaged PDF.",
            "Password-protected or malformed documents may be rejected.",
            "Raster export converts vector text and graphics into pixels and should only be used when required.",
        ],
        "privacy": [
            "Any PDF is welcome — official, administrative, personal, or technical. There is no restriction on the subject of your document.",
            "Uploads are held only in server memory for the lifetime of your request and are deleted the moment the result is returned.",
            "Nothing is written to a database, an audit log, or a shared folder, and no copy is retained after the download completes.",
            "The service runs entirely on office intranet hardware. No document, page, or fragment is ever transmitted to the public internet or to any third-party service.",
        ],
        "diagram": "help/pdf-tools-workflow.svg",
    },
    "tabular-ml": {
        "purpose": "Guide classification and regression from a CSV/XLSX table through profiling, leakage-aware preparation, reproducible model comparison, diagnostics, and inference.",
        "workflow": [
            "Load and profile the table",
            "Choose target, task, features, and split policy",
            "Fit preprocessing only on training folds",
            "Cross-validate and compare CPU models",
            "Evaluate held-out data, explain results, and export the fitted pipeline",
        ],
        "equations": [
            {
                "name": "Standardization",
                "tex": r"z_{j} \;=\; \frac{x_{j} - \mu_{j}}{\sigma_{j}}",
                "plain": "z_j equals x_j minus mu_j, divided by sigma_j",
                "meaning": "Training-fold mean and standard deviation scale numeric feature j; validation data must not influence them.",
                "where": [
                    (r"x_{j}", "raw value of numeric feature j"),
                    (r"\mu_{j},\,\sigma_{j}", "mean and standard deviation from the training folds only"),
                ],
            },
            {
                "name": "Coefficient of determination",
                "tex": (
                    r"R^{2} \;=\; 1 \;-\; \frac{\displaystyle\sum_{i}\bigl(y_{i}-\hat{y}_{i}\bigr)^{2}}"
                    r"{\displaystyle\sum_{i}\bigl(y_{i}-\bar{y}\bigr)^{2}}"
                ),
                "plain": (
                    "R squared equals one minus the sum of squared residuals "
                    "divided by the total sum of squares"
                ),
                "meaning": "Explained variance relative to simply predicting the target mean.",
                "where": [
                    (r"y_{i},\,\hat{y}_{i}", "observed and predicted target for sample i"),
                    (r"\bar{y}", "mean of the observed target"),
                ],
            },
            {
                "name": "F1 score",
                "tex": (
                    r"\begin{gathered}"
                    r"F_{1} \;=\; \frac{2\,P\,R}{P + R} \\[6pt]"
                    r"P = \frac{TP}{TP + FP}, \qquad R = \frac{TP}{TP + FN}"
                    r"\end{gathered}"
                ),
                "plain": (
                    "F1 equals two P R divided by P plus R, where P is precision "
                    "and R is recall"
                ),
                "meaning": "Balances false-positive and false-negative performance in a single classification number.",
                "where": [
                    (r"P,\,R", "precision and recall"),
                    (r"TP,\,FP,\,FN", "true positives, false positives, false negatives"),
                ],
            },
            {
                "name": "Cross-validated estimate",
                "tex": r"\widehat{\mathrm{CV}} \;=\; \frac{1}{K}\sum_{k=1}^{K} m\bigl(f_{-k},\, D_{k}\bigr)",
                "plain": (
                    "the cross-validated estimate equals one over K times the sum "
                    "over k of the metric of the model trained without fold k, evaluated on fold k"
                ),
                "meaning": "Each fold is scored by a model that never saw it, which is what makes the estimate honest.",
                "where": [
                    (r"K", "number of folds"),
                    (r"f_{-k}", "model fitted on every fold except k"),
                    (r"D_{k}", "held-out data of fold k"),
                ],
            },
        ],
        "inputs": [
            (
                "Target and task",
                "Define what is predicted and whether metrics/models are classification or regression appropriate.",
            ),
            (
                "Feature columns",
                "Carry the evidence available at prediction time; IDs, future information, or target proxies cause leakage.",
            ),
            (
                "Split and cross-validation policy",
                "Determine how honestly the workflow estimates generalization.",
            ),
            (
                "Preprocessing and hyperparameters",
                "Control imputation, encoding, scaling, model capacity, regularization, and runtime.",
            ),
        ],
        "limits": [
            "Association is not causation, and predictive importance is not a physical mechanism.",
            "Small, imbalanced, grouped, or time-ordered datasets need an appropriate split strategy.",
            "The final claim must be based on untouched held-out data, not the best cross-validation score alone.",
        ],
        "diagram": "help/tabular-ml-workflow.svg",
    },
    "scientific-calculator": {
        "purpose": "Safely evaluate bounded mathematical expressions with named variables and create reproducible one- or two-variable numerical plots.",
        "workflow": [
            "Parse the expression into an abstract syntax tree",
            "Reject unapproved syntax and unknown functions",
            "Bind constants, variables, and angle convention",
            "Evaluate finite numeric results over one point or a bounded grid",
            "Return the canonical expression, values, and plot data",
        ],
        "equations": [
            {
                "name": "Uniform sampling",
                "tex": r"x_{k} \;=\; x_{0} + k\,\Delta x,\qquad k = 0,1,\dots,N-1",
                "plain": "x_k equals x_0 plus k times delta x, for k from zero to N minus one",
                "meaning": "A one-dimensional plot evaluates the same validated expression on a bounded uniform grid.",
                "where": [
                    (r"x_{0}", "start of the plotted range"),
                    (r"\Delta x", "positive step size"),
                    (r"N", "number of sampled points, capped by the point limit"),
                ],
            },
            {
                "name": "Sample count",
                "tex": r"N \;=\; \left\lfloor \frac{x_{\text{stop}} - x_{0}}{\Delta x} \right\rfloor + 1",
                "plain": (
                    "N equals the floor of x stop minus x zero over delta x, plus one"
                ),
                "meaning": "Determines plot resolution and is checked against the maximum allowed number of points.",
                "where": [
                    (r"x_{\text{stop}}", "end of the plotted range"),
                ],
            },
            {
                "name": "Degree-mode conversion",
                "tex": r"\sin_{\deg}(\alpha) \;=\; \sin\!\left(\frac{\pi\,\alpha}{180}\right)",
                "plain": "sine in degrees of alpha equals sine of pi alpha over 180",
                "meaning": "Degree mode converts trigonometric inputs before applying the standard radian functions.",
                "where": [
                    (r"\alpha", "angle supplied in degrees"),
                ],
            },
        ],
        "inputs": [
            (
                "Expression",
                "Defines numeric operators, approved functions, constants, and named variables; ^ is normalized to exponentiation.",
            ),
            (
                "Variable bindings",
                "Provide finite numeric values for every non-constant symbol.",
            ),
            (
                "Angle unit",
                "Determines whether trigonometric arguments and inverse-trigonometric results use radians or degrees.",
            ),
            (
                "Plot ranges",
                "Start, stop, and positive step determine sampling density and must remain within the point limit.",
            ),
        ],
        "limits": [
            "This is a floating-point numerical calculator, not a symbolic algebra system.",
            "Inputs carrying physical units should be handled by Unit Converter.",
            "A plotted curve demonstrates the sampled expression; it does not establish model validity between or beyond those samples.",
            "In the periodic table, a property shown as not measured has genuinely never been measured rather than merely being absent here; no melting point, boiling point or density exists for elements 100 to 118, because none has been produced in a weighable amount.",
        ],
        "diagram": "help/scientific-calculator-workflow.svg",
    },
    "unit-converter": {
        "purpose": "Convert physical quantities only between dimensionally compatible units and evaluate compound-unit expressions with an explicit unit registry.",
        "workflow": [
            "Parse the magnitude and source unit",
            "Resolve aliases into registry definitions",
            "Check dimensional compatibility",
            "Apply scale and any offset transformation",
            "Format the converted magnitude and canonical target unit",
        ],
        "equations": [
            {
                "name": "Linear conversion",
                "tex": r"x_{B} \;=\; x_{A}\,\frac{s_{A}}{s_{B}}",
                "plain": "x_B equals x_A times s_A over s_B",
                "meaning": "For multiplicative units, base-unit scale factors convert the same physical quantity.",
                "where": [
                    (r"x_{A},\,x_{B}", "magnitude in the source and target unit"),
                    (r"s_{A},\,s_{B}", "scale of each unit relative to the base unit"),
                ],
            },
            {
                "name": "Affine temperature",
                "tex": r"T_{\mathrm{K}} \;=\; T_{^{\circ}\mathrm{C}} + 273.15",
                "plain": "T in kelvin equals T in degrees Celsius plus 273.15",
                "meaning": "Absolute temperature scales include an offset; temperature intervals do not.",
                "where": [
                    (r"T_{\mathrm{K}}", "absolute thermodynamic temperature"),
                    (r"T_{^{\circ}\mathrm{C}}", "the same temperature on the Celsius scale"),
                ],
            },
            {
                "name": "Dimensional condition",
                "tex": (
                    r"\dim\bigl(q_{\text{source}}\bigr) \;=\; \dim\bigl(q_{\text{target}}\bigr)"
                    r" \;=\; \mathsf{L}^{\alpha}\mathsf{M}^{\beta}\mathsf{T}^{\gamma}\cdots"
                ),
                "plain": (
                    "the dimension of the source quantity equals the dimension of the "
                    "target quantity, expressed as powers of the base dimensions"
                ),
                "meaning": "Conversion is valid only when source and target dimensionalities match exactly.",
                "where": [
                    (r"\mathsf{L},\mathsf{M},\mathsf{T}", "base dimensions of length, mass, and time"),
                    (r"\alpha,\beta,\gamma", "integer exponents of each base dimension"),
                ],
            },
        ],
        "inputs": [
            ("Magnitude", "The numeric value to transform."),
            (
                "Source and target units",
                "Define the dimensionality, scale factors, and possible offsets.",
            ),
            (
                "Absolute or interval temperature",
                "Distinguishes a thermodynamic temperature from a temperature difference.",
            ),
            (
                "Compound expression",
                "Combines quantities through multiplication or division while preserving dimensions.",
            ),
        ],
        "limits": [
            "A unit conversion cannot validate whether the underlying physical quantity or measurement is correct.",
            "Absolute and interval temperatures must not be mixed.",
            "Ambiguous abbreviations should be replaced with explicit unit names before reporting a result.",
        ],
        "diagram": "help/unit-converter-workflow.svg",
    },
}


def tool_help(tool_id: str) -> dict[str, Any] | None:
    """Return help content for a released tool, or ``None`` for an unknown ID."""
    return TOOL_HELP.get(tool_id)
