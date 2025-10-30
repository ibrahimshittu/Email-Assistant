#!/usr/bin/env python3
"""
Script to fix imports after reorganizing backend structure
"""
import re
from pathlib import Path

# Define import replacements
REPLACEMENTS = [
    # Database imports
    (r'from \.\.db import', 'from ..database import'),
    (r'from \.db import', 'from .database import'),
    (r'from backend\.db import', 'from database import'),

    # Models imports
    (r'from \.\.models import', 'from ..database.models import'),
    (r'from \.models import', 'from .database.models import'),
    (r'from backend\.models import', 'from database import'),
    (r'from backend\.database\.models import', 'from database import'),

    # Services imports - nylas
    (r'from \.\.nylas_client import', 'from ..services.nylas_client import'),
    (r'from \.nylas_client import', 'from .services.nylas_client import'),
    (r'from backend\.nylas_client import', 'from services.nylas_client import'),

    # Services imports - vectorstore
    (r'from \.\.vectorstore import', 'from ..services.vectorstore import'),
    (r'from \.vectorstore import', 'from .services.vectorstore import'),
    (r'from backend\.vectorstore import', 'from services.vectorstore import'),

    # Services imports - ingest
    (r'from \.\.ingest import', 'from ..services.ingest import'),
    (r'from \.ingest import', 'from .services.ingest import'),
    (r'from backend\.ingest import', 'from services.ingest import'),

    # Services imports - eval
    (r'from \.\.eval import', 'from ..services.eval import'),
    (r'from \.eval import', 'from .services.eval import'),
    (r'from backend\.eval import', 'from services.eval import'),
]

def fix_file(filepath: Path):
    """Fix imports in a single file"""
    content = filepath.read_text()
    original_content = content

    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        filepath.write_text(content)
        print(f"✓ Fixed: {filepath}")
        return True
    return False

def main():
    backend_dir = Path(__file__).resolve().parents[1] / "backend"
    scripts_dir = Path(__file__).resolve().parent

    # Find all Python files in backend and scripts
    py_files = list(backend_dir.rglob("*.py")) + list(scripts_dir.rglob("*.py"))

    fixed_count = 0
    for py_file in py_files:
        if "__pycache__" in str(py_file):
            continue
        if fix_file(py_file):
            fixed_count += 1

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
