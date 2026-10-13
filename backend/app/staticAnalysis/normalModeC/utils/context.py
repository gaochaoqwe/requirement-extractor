from typing import Any, Dict


_task_context_map: Dict[int, Dict[str, Any]] = {}


def set_normal_mode_c_context(task_id: int, context: Dict[str, Any]) -> None:
    payload = dict(context or {})
    payload["domain"] = "normalModeC"
    _task_context_map[task_id] = payload


def get_normal_mode_c_context(task_id: int) -> Dict[str, Any]:
    return dict(_task_context_map.get(task_id, {}))


def clear_normal_mode_c_context(task_id: int) -> None:
    _task_context_map.pop(task_id, None)
