from enum import Enum


class TripType(str, Enum):
    OUTBOUND = "Outbound"
    INBOUND = "Inbound"
