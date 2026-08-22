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
            "summary": "Preview, reorder, merge, and extract pages from research PDFs.",
            "category": "Productivity",
            "tags": ["PDF", "merge", "extract"],
            "state": "active",
            "owner": "pdf_tools",
            "href": "/pdf_tools/",
            "icon": "pdf_tools_icon.png",
            "internal": True,
        },
        {
            "id": "scientific-calculator",
            "name": "Scientific Calculator",
            "summary": "Evaluate expressions with variables, functions, and engineering plots.",
            "category": "Productivity",
            "tags": ["units", "trigonometry", "constants"],
            "state": "active",
            "owner": "scientific_calculator",
            "href": os.getenv(
                "SCIENTIFIC_CALCULATOR_URL", "http://127.0.0.1:5055"
            ),
            "icon": "calculator-mark.svg",
            "internal": False,
        },
        {
            "id": "unit-converter",
            "name": "Unit Converter",
            "summary": "Convert engineering units and evaluate dimensional expressions.",
            "category": "Productivity",
            "tags": ["units", "engineering", "conversion"],
            "state": "active",
            "owner": "unit_converter",
            "href": os.getenv("UNIT_CONVERTER_URL", "http://127.0.0.1:5065"),
            "icon": "calculator-mark.svg",
            "internal": False,
        },
    ]
