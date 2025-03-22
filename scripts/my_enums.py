from enum import Enum

class TripType(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
