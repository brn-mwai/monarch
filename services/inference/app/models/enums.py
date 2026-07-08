"""Enum types shared across the API surface."""

from enum import Enum


class Modality(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"


class NAAClassification(str, Enum):
    LOW = "LOW"
    MOD = "MOD"
    HIGH = "HIGH"
    UNDEFINED = "UNDEFINED"
