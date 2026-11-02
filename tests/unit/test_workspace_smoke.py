"""Smoke tests for workspace package installation."""

from importlib import import_module

PACKAGE_MODULES = (
    "rag_core",
    "rag_core.eval",
    "rag_core.generation",
    "rag_core.ingestion",
    "rag_core.ingestion.chunking",
    "rag_core.llm",
    "rag_core.llm.providers",
    "rag_core.retrieval",
    "indonesian_labor_regulations",
)


def test_workspace_packages_are_importable() -> None:
    for module_name in PACKAGE_MODULES:
        import_module(module_name)
