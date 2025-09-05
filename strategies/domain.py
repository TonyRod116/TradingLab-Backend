"""
Domain models and enums for trading strategies
"""
from enum import Enum


class QCStatus(str, Enum):
    """QuantConnect status enumeration"""
    QUEUED = "Queued"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    ABORTED = "Aborted"
    UNKNOWN = "Unknown"


def normalize_status(raw) -> QCStatus:
    """
    Normalize raw status string to QCStatus enum.
    
    Args:
        raw: Raw status value from QuantConnect API
        
    Returns:
        Normalized QCStatus enum value
        
    Example:
        >>> normalize_status("running")  # Returns QCStatus.RUNNING
        >>> normalize_status("Error")  # Returns QCStatus.FAILED
        >>> normalize_status("weird")  # Returns QCStatus.UNKNOWN
    """
    if not raw:
        return QCStatus.UNKNOWN
    
    s = str(raw).strip().lower()
    
    if s in ("queued",):
        return QCStatus.QUEUED
    if s in ("running",):
        return QCStatus.RUNNING
    if s in ("completed", "complete"):
        return QCStatus.COMPLETED
    if s in ("failed", "error"):
        return QCStatus.FAILED
    if s in ("aborted", "abort"):
        return QCStatus.ABORTED
    
    return QCStatus.UNKNOWN
