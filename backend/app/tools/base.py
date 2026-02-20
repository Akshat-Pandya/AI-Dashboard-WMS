from typing import Dict, Any
from sqlalchemy.orm import Session

class ToolResult(Dict[str, Any]):
    pass

class BaseTool:
    name: str

    def run(self, db: Session, params: dict | None = None) -> ToolResult:
        raise NotImplementedError