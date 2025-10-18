"""
Dynamic rubric management system.
Allows creation, updating, and management of rubrics without code changes.
"""

import json
import yaml
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from .models import DynamicRubric, RubricCriterion


class RubricManager:
    """Manages dynamic rubrics with persistence to file system."""
    
    def __init__(self, rubrics_dir: Path = Path("data/rubrics")):
        self.rubrics_dir = rubrics_dir
        self.rubrics_dir.mkdir(parents=True, exist_ok=True)
        self._rubrics_cache: Dict[str, DynamicRubric] = {}
        self._load_all_rubrics()
    
    def _load_all_rubrics(self) -> None:
        """Load all rubrics from the rubrics directory."""
        for rubric_file in self.rubrics_dir.glob("*.json"):
            try:
                with rubric_file.open("r", encoding="utf-8") as f:
                    rubric_data = json.load(f)
                    rubric = DynamicRubric(**rubric_data)
                    self._rubrics_cache[rubric.id] = rubric
            except Exception as e:
                print(f"Warning: Could not load rubric {rubric_file}: {e}")
    
    def create_rubric(
        self, 
        rubric_id: str, 
        name: str, 
        description: str, 
        criteria: List[RubricCriterion]
    ) -> DynamicRubric:
        """Create a new rubric."""
        if rubric_id in self._rubrics_cache:
            raise ValueError(f"Rubric with ID {rubric_id} already exists")
        
        rubric = DynamicRubric(
            id=rubric_id,
            name=name,
            description=description,
            criteria=criteria
        )
        
        self._save_rubric(rubric)
        self._rubrics_cache[rubric_id] = rubric
        return rubric
    
    def update_rubric(
        self, 
        rubric_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        criteria: Optional[List[RubricCriterion]] = None
    ) -> DynamicRubric:
        """Update an existing rubric."""
        if rubric_id not in self._rubrics_cache:
            raise ValueError(f"Rubric with ID {rubric_id} not found")
        
        rubric = self._rubrics_cache[rubric_id]
        
        if name is not None:
            rubric.name = name
        if description is not None:
            rubric.description = description
        if criteria is not None:
            rubric.criteria = criteria
        
        rubric.updated_at = datetime.utcnow()
        
        self._save_rubric(rubric)
        return rubric
    
    def get_rubric(self, rubric_id: str) -> Optional[DynamicRubric]:
        """Get a rubric by ID."""
        return self._rubrics_cache.get(rubric_id)
    
    def list_rubrics(self) -> List[DynamicRubric]:
        """List all available rubrics."""
        return list(self._rubrics_cache.values())
    
    def delete_rubric(self, rubric_id: str) -> bool:
        """Delete a rubric."""
        if rubric_id not in self._rubrics_cache:
            return False
        
        rubric_file = self.rubrics_dir / f"{rubric_id}.json"
        if rubric_file.exists():
            rubric_file.unlink()
        
        del self._rubrics_cache[rubric_id]
        return True
    
    def _save_rubric(self, rubric: DynamicRubric) -> None:
        """Save a rubric to file."""
        rubric_file = self.rubrics_dir / f"{rubric.id}.json"
        with rubric_file.open("w", encoding="utf-8") as f:
            json.dump(rubric.model_dump(mode='json'), f, indent=2, default=str)
    
    def export_rubric(self, rubric_id: str, format: str = "json") -> str:
        """Export a rubric in specified format."""
        rubric = self.get_rubric(rubric_id)
        if not rubric:
            raise ValueError(f"Rubric {rubric_id} not found")
        
        if format == "json":
            return json.dumps(rubric.model_dump(mode='json'), indent=2, default=str)
        elif format == "yaml":
            return yaml.dump(rubric.model_dump(mode='json'), default_flow_style=False, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def validate_rubric_weights(self, rubric_id: str) -> bool:
        """Validate that rubric criterion weights sum to 1.0."""
        rubric = self.get_rubric(rubric_id)
        if not rubric:
            return False
        
        total_weight = sum(criterion.weight for criterion in rubric.criteria)
        return abs(total_weight - 1.0) < 0.001  # Allow small floating point errors
