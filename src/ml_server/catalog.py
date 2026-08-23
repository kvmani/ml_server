"""Reviewed, data-driven catalog for the platform landing page."""

from __future__ import annotations

import os
from typing import Any


def tool_catalog() -> list[dict[str, Any]]:
    """Return only services approved for the current platform release."""
    return [
        {
            "id": "hydride-segmentation",
            "name": "Hydride Segmentation",
            "summary": "Measure hydride morphology and distributions from micrographs.",
            "detail": (
                "An AI-assisted advanced segmentation tool for identifying, reviewing, "
                "and quantifying hydrides and other microstructural features."
            ),
            "category": "Microstructure",
            "tags": ["segmentation", "microstructure", "zirconium"],
            "state": "active",
            "owner": "HydrideSegmentation",
            "href": os.getenv("HYDRIDE_SEGMENTATION_URL", "http://127.0.0.1:5005"),
            "icon": "micrograph-mark.svg",
            "internal": False,
        },
        {
            "id": "pytex",
            "name": "PyTex Workbench",
            "summary": "Texture, diffraction, EBSD, TEM, and crystallographic analysis.",
            "detail": (
                "A convention-explicit crystallography workbench for orientation, texture, "
                "diffraction, microscopy, and phase-transformation workflows."
            ),
            "category": "Crystallography",
            "tags": ["texture", "diffraction", "EBSD", "TEM"],
            "state": "active",
            "owner": "pytex",
            "href": os.getenv("PYTEX_URL", "http://127.0.0.1:8765"),
            "icon": "pytex-mark.svg",
            "internal": False,
        },
        {
            "id": "pdf-tools",
            "name": "PDF Tools",
            "summary": "Preview, reorder, merge, split, and extract pages from any PDF.",
            "detail": (
                "A general-purpose PDF workbench for every kind of document — reports, scans, "
                "forms, presentations, or manuscripts. Files are processed in memory on this "
                "intranet server, are never stored, and never leave the office network."
            ),
            "category": "Productivity",
            "tags": [
                "PDF",
                "merge",
                "split",
                "extract",
                "reorder",
                "documents",
                "scans",
                "forms",
                "any pdf",
                "private",
            ],
            "state": "active",
            "owner": "pdf_tools",
            "href": "/pdf_tools/",
            "icon": "pdf_tools_icon.png",
            "internal": True,
        },
        {
            "id": "tabular-ml",
            "name": "Tabular ML Workbench",
            "summary": (
                "Explore tables, prepare features, compare models, and explain "
                "classification or regression results."
            ),
            "detail": (
                "A guided, CPU-only machine-learning workflow with leakage-aware preparation, "
                "model comparison, validation metrics, and interpretable predictions."
            ),
            "category": "Data Science",
            "tags": [
                "machine learning",
                "CSV",
                "Excel",
                "classification",
                "regression",
            ],
            "state": "active",
            "owner": "tabular_ml",
            "href": "/tabular_ml/",
            "icon": "tabular-ml-mark.svg",
            "internal": True,
        },
        {
            "id": "scientific-calculator",
            "name": "Scientific Calculator",
            "summary": "Evaluate expressions with variables, functions, and engineering plots.",
            "detail": (
                "A safe numerical expression engine for reproducible scalar calculations and "
                "bounded one- or two-variable engineering plots."
            ),
            "category": "Productivity",
            "tags": ["units", "trigonometry", "constants"],
            "state": "active",
            "owner": "scientific_calculator",
            "href": os.getenv("SCIENTIFIC_CALCULATOR_URL", "http://127.0.0.1:5055"),
            "icon": "calculator-mark.svg",
            "internal": False,
        },
        {
            "id": "unit-converter",
            "name": "Unit Converter",
            "summary": "Convert engineering units and evaluate dimensional expressions.",
            "detail": (
                "A dimension-aware engineering converter for quantities, compound units, "
                "temperature scales, and auditable unit expressions."
            ),
            "category": "Productivity",
            "tags": ["units", "engineering", "conversion"],
            "state": "active",
            "owner": "unit_converter",
            "href": os.getenv("UNIT_CONVERTER_URL", "http://127.0.0.1:5065"),
            "icon": "calculator-mark.svg",
            "internal": False,
        },
    ]
