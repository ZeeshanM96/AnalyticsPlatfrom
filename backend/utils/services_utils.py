#  This file contains utility functions for building datasets for alert charts.
from collections import defaultdict
from fastapi import HTTPException
from backend.utils.constants import VALID_ROLES


def validate_preferences(preferences: list):
    if not preferences:
        raise HTTPException(status_code=400, detail="No preferences provided")


def validate_signup_data(req):
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role selected")
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if req.role == "Client" and req.source == "AWS":
        raise HTTPException(
            status_code=400, detail="Clients cannot choose 'AWS' as a source"
        )
    if not req.source:
        raise HTTPException(status_code=400, detail="Source is required")


def build_alert_chart_dataset(rows: list[tuple]) -> dict:
    result = defaultdict(lambda: defaultdict(int))
    batch_set = set()

    for batch_id, alert_type, count in rows:
        result[alert_type][batch_id] = count
        batch_set.add(batch_id)

    sorted_batches = sorted(batch_set)
    datasets = []
    for alert_type, batch_counts in result.items():
        datasets.append(
            {
                "label": alert_type,
                "data": [batch_counts.get(bid, 0) for bid in sorted_batches],
                "borderWidth": 2,
                "fill": False,
            }
        )

    return {"labels": sorted_batches, "datasets": datasets}


def build_source_metric_datasets(rows, source_map: dict[int, str]) -> dict:
    grouped = {}
    for source_id, event_type, total in rows:
        source_name = source_map.get(source_id, f"Unknown-{source_id}")
        if event_type not in grouped:
            grouped[event_type] = {}
        grouped[event_type][source_name] = total

    all_sources = sorted({s for group in grouped.values() for s in group.keys()})
    datasets = []

    for event_type, source_totals in grouped.items():
        datasets.append(
            {
                "label": event_type,
                "data": [source_totals.get(s, 0) for s in all_sources],
            }
        )

    return {"labels": all_sources, "datasets": datasets}


def build_service_metric_dataset(rows):
    all_dates = set()
    grouped = defaultdict(lambda: defaultdict(float))

    for day, service_name, metric_type, value in rows:
        label = f"{service_name} - {metric_type}"
        date_str = day.strftime("%Y-%m-%d")
        grouped[label][date_str] = value
        all_dates.add(date_str)

    sorted_dates = sorted(all_dates)
    datasets = []

    for label, values in grouped.items():
        datasets.append(
            {
                "label": label,
                "data": [values.get(date, 0) for date in sorted_dates],
                "fill": False,
                "borderWidth": 2,
            }
        )

    return {"labels": sorted_dates, "datasets": datasets}


def build_event_dataset(rows):
    data = defaultdict(lambda: defaultdict(int))
    all_dates = set()

    for date_val, event_type, count in rows:
        date_str = date_val.strftime("%Y-%m-%d")
        data[event_type][date_str] = count
        all_dates.add(date_str)

    sorted_dates = sorted(all_dates)
    datasets = []
    for event_type, date_counts in data.items():
        datasets.append(
            {
                "label": event_type,
                "data": [date_counts.get(date, 0) for date in sorted_dates],
                "fill": False,
                "borderWidth": 2,
            }
        )

    return {"labels": sorted_dates, "datasets": datasets}


def build_resolution_summary_dataset(rows):
    severity_levels = ["Critical", "Info", "Warning"]
    resolved_map = defaultdict(lambda: defaultdict(int))
    unresolved_map = defaultdict(lambda: defaultdict(int))
    sources_set = set()

    for source, severity, status, count in rows:
        sources_set.add(source)
        if status == "Resolved":
            resolved_map[severity][source] += count
        else:
            unresolved_map[severity][source] += count

    sorted_sources = sorted(sources_set)
    labels = sorted_sources

    color_map = {
        "Critical-Resolved": "#5cb85c",
        "Critical-Unresolved": "#d9534f",
        "Info-Resolved": "#5bc0de",
        "Info-Unresolved": "#dff0d8",
        "Warning-Resolved": "#f7ecb5",
        "Warning-Unresolved": "#f0ad4e",
    }

    def get_data(map_, severity):
        return [map_[severity].get(source, 0) for source in labels]

    datasets = []
    for severity in severity_levels:
        datasets.append(
            {
                "label": f"{severity} - Resolved",
                "backgroundColor": color_map.get(f"{severity}-Resolved", "#ccc"),
                "data": get_data(resolved_map, severity),
                "stack": severity,
            }
        )
        datasets.append(
            {
                "label": f"{severity} - Unresolved",
                "backgroundColor": color_map.get(f"{severity}-Unresolved", "#ccc"),
                "data": get_data(unresolved_map, severity),
                "stack": severity,
            }
        )

    return {"labels": labels, "datasets": datasets}
