"""Stable imports for existing callers of the knowledge layer."""

from .dataset_io import DEFAULT_DATASET, DEFAULT_ONTOLOGY, ROOT, TABLES, KnowledgeError, read_json, write_json
from .importer import import_dataset
from .queries import KnowledgeStore
from .validation import ID_PATTERN, validate

__all__ = [
    "DEFAULT_DATASET", "DEFAULT_ONTOLOGY", "ROOT", "TABLES", "ID_PATTERN", "KnowledgeError",
    "KnowledgeStore", "import_dataset", "read_json", "validate", "write_json",
]
