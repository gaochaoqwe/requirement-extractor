import os
import logging
from typing import Callable, Optional

from sqlalchemy.orm import Session

from backend.app.databaseManage.dynamicDatabaseManage.services.intelligent_export_service import (
    IntelligentExportService,
)

logger = logging.getLogger(__name__)


class AssetReuseExportService:
    @staticmethod
    def run_export(
        db: Session,
        file_content: bytes,
        selected_type: str,
        selected_software_type: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> bytes:
        return IntelligentExportService.process_intelligent_export_with_progress(
            db=db,
            file_content=file_content,
            selected_type=selected_type,
            selected_software_type=selected_software_type,
            progress_callback=progress_callback,
        )


def ensure_output_dir(file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
