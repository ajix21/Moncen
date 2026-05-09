from config import ALERT_LEVELS


def get_alert_level(person_count: int) -> tuple[str, str]:
    """Return (level_name, hex_color) for a given person count."""
    for level, cfg in ALERT_LEVELS.items():
        if cfg["min"] <= person_count <= cfg["max"]:
            return level, cfg["color"]
    return "DARURAT", ALERT_LEVELS["DARURAT"]["color"]


def should_log_event(alert_level: str, previous_level: str | None) -> bool:
    """Log when alert level changes or when it's not NORMAL."""
    if alert_level != "NORMAL":
        return True
    if previous_level and previous_level != alert_level:
        return True
    return False
