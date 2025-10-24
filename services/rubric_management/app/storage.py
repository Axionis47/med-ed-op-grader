"""Storage layer for rubrics using JSON files."""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil

# Add parent directories to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import Rubric


class RubricStorage:
    """Handles storage and retrieval of rubrics from JSON files."""
    
    def __init__(self, storage_dir: str = "data/rubrics"):
        """
        Initialize rubric storage.
        
        Args:
            storage_dir: Directory to store rubric JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_rubric_path(self, rubric_id: str, version: str) -> Path:
        """Get file path for a specific rubric version."""
        return self.storage_dir / f"{rubric_id}_v{version}.json"
    
    def _get_latest_version_path(self, rubric_id: str, status: str = "approved") -> Optional[Path]:
        """Get path to the latest version of a rubric with given status."""
        # Find all versions of this rubric
        pattern = f"{rubric_id}_v*.json"
        matching_files = list(self.storage_dir.glob(pattern))
        
        if not matching_files:
            return None
        
        # Load each file and filter by status
        approved_versions = []
        for file_path in matching_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('status') == status:
                        approved_versions.append((data.get('version'), file_path))
            except (json.JSONDecodeError, IOError):
                continue
        
        if not approved_versions:
            return None
        
        # Sort by version (semantic versioning)
        def version_key(version_str: str) -> tuple:
            parts = version_str.split('.')
            return tuple(int(p) for p in parts)
        
        approved_versions.sort(key=lambda x: version_key(x[0]), reverse=True)
        return approved_versions[0][1]
    
    def save(self, rubric: Rubric) -> None:
        """
        Save a rubric to storage.
        
        Args:
            rubric: Rubric to save
        """
        file_path = self._get_rubric_path(rubric.rubric_id, rubric.version)
        
        # Update timestamp
        rubric.updated_at = datetime.utcnow()
        
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(rubric.model_dump(mode='json'), f, indent=2, default=str)
    
    def load(self, rubric_id: str, version: Optional[str] = None) -> Optional[Rubric]:
        """
        Load a rubric from storage.
        
        Args:
            rubric_id: Rubric identifier
            version: Specific version to load (latest approved if None)
        
        Returns:
            Rubric object or None if not found
        """
        if version:
            file_path = self._get_rubric_path(rubric_id, version)
        else:
            file_path = self._get_latest_version_path(rubric_id, status="approved")
        
        if not file_path or not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return Rubric(**data)
        except (json.JSONDecodeError, IOError, ValueError):
            return None
    
    def list_versions(self, rubric_id: str) -> list[dict]:
        """
        List all versions of a rubric.
        
        Args:
            rubric_id: Rubric identifier
        
        Returns:
            List of version metadata
        """
        pattern = f"{rubric_id}_v*.json"
        matching_files = list(self.storage_dir.glob(pattern))
        
        versions = []
        for file_path in matching_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    versions.append({
                        'version': data.get('version'),
                        'status': data.get('status'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                    })
            except (json.JSONDecodeError, IOError):
                continue
        
        # Sort by version
        def version_key(version_str: str) -> tuple:
            parts = version_str.split('.')
            return tuple(int(p) for p in parts)
        
        versions.sort(key=lambda x: version_key(x['version']), reverse=True)
        return versions
    
    def delete(self, rubric_id: str, version: str) -> bool:
        """
        Delete a specific rubric version.
        
        Args:
            rubric_id: Rubric identifier
            version: Version to delete
        
        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_rubric_path(rubric_id, version)
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def create_new_version(self, rubric: Rubric) -> str:
        """
        Create a new version of a rubric by incrementing the patch version.
        
        Args:
            rubric: Current rubric
        
        Returns:
            New version string
        """
        parts = rubric.version.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Increment patch version
        new_version = f"{major}.{minor}.{patch + 1}"
        return new_version
    
    def backup_rubric(self, rubric_id: str, version: str) -> Optional[Path]:
        """
        Create a backup of a rubric version.
        
        Args:
            rubric_id: Rubric identifier
            version: Version to backup
        
        Returns:
            Path to backup file or None if source not found
        """
        source_path = self._get_rubric_path(rubric_id, version)
        
        if not source_path.exists():
            return None
        
        backup_dir = self.storage_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{rubric_id}_v{version}_{timestamp}.json"
        
        shutil.copy2(source_path, backup_path)
        return backup_path

