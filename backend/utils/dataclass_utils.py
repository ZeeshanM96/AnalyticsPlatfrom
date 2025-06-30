from dataclasses import dataclass
from typing import Optional


@dataclass
class AlertSummaryFilter:
    source_id: int
    from_date: str
    to_date: str
    batch_ids: Optional[list[str]] = None
    severities: Optional[list[str]] = None
    is_admin: bool = False


@dataclass
class AlertResolutionFilter:
    from_date: str
    to_date: str
    source_id: int
    event_types: Optional[list[str]] = None
    is_admin: bool = False
