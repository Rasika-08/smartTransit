from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

# ==================================================
# ORGANIZATION SCHEMAS
# ==================================================

class OrganizationCreate(BaseModel):
    name: str
    email: str
    phone: str
    address: str


class OrganizationResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    address: str

    class Config:
        from_attributes = True


# ==================================================
# BUS SCHEMAS
# ==================================================

class BusCreate(BaseModel):
    organization_id: int
    bus_number: str
    registration_number: str
    capacity: int
    bus_type: str
    status: str = "AVAILABLE"


class BusResponse(BaseModel):
    id: int
    organization_id: int
    bus_number: str
    registration_number: str
    capacity: int
    bus_type: str
    status: str

    class Config:
        from_attributes = True


# ==================================================
# CREW SCHEMAS
# ==================================================

class CrewCreate(BaseModel):
    organization_id: int
    name: str
    employee_id: str
    role: str
    phone: str
    status: str = "AVAILABLE"


class CrewResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    employee_id: str
    role: str
    phone: str
    status: str

    class Config:
        from_attributes = True


# ==================================================
# STOP SCHEMAS
# ==================================================

class StopCreate(BaseModel):
    organization_id: int
    name: str
    latitude: float
    longitude: float


class StopResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True


# ==================================================
# ROUTE STOP SCHEMAS
# ==================================================

class RouteStopResponse(BaseModel):
    id: int
    route_id: int
    stop_id: int
    sequence_number: int

    class Config:
        from_attributes = True


# ==================================================
# ROUTE SCHEMAS
# ==================================================

class RouteCreate(BaseModel):
    organization_id: int
    route_number: str
    route_name: str
    start_location: Optional[str] = None
    end_location: Optional[str] = None
    distance: Optional[float] = None
    estimated_duration: Optional[int] = None
    status: str = "ACTIVE"

    # Stop IDs in the order in which the bus travels
    stop_ids: List[int]


class RouteResponse(BaseModel):
    id: int
    organization_id: int
    route_number: str
    route_name: str
    start_location: Optional[str]
    end_location: Optional[str]
    distance: Optional[float]
    estimated_duration: Optional[int]
    status: str
    route_stops: List[RouteStopResponse] = []

    class Config:
        from_attributes = True
# ==================================================
# TRIP SCHEMAS
# ==================================================

class TripCreate(BaseModel):
    organization_id: int
    route_id: int

    bus_id: Optional[int] = None
    driver_id: Optional[int] = None
    conductor_id: Optional[int] = None

    trip_date: datetime
    departure_time: datetime
    arrival_time: datetime

    status: str = "SCHEDULED"
    direction: str = "OUTBOUND"


class TripResponse(BaseModel):
    id: int
    organization_id: int
    route_id: int

    bus_id: Optional[int]
    driver_id: Optional[int]
    conductor_id: Optional[int]

    trip_date: datetime
    departure_time: datetime
    arrival_time: datetime

    status: str
    direction: str

    class Config:
        from_attributes = True
# ==================================================
# SCHEDULE SCHEMAS
# ==================================================

class ScheduleCreate(BaseModel):
    organization_id: int
    trip_id: int
    bus_id: int
    driver_id: int
    conductor_id: int

    scheduled_date: datetime
    start_time: datetime
    end_time: datetime

    duty_type: str = "LINKED"
    status: str = "SCHEDULED"


class ScheduleResponse(BaseModel):
    id: int
    organization_id: int
    trip_id: int
    bus_id: int
    driver_id: int
    conductor_id: int

    scheduled_date: datetime
    start_time: datetime
    end_time: datetime

    duty_type: str
    status: str

    class Config:
        from_attributes = True
# ==================================================
# DUTY SCHEMAS
# ==================================================

class DutyCreate(BaseModel):
    organization_id: int
    duty_name: str
    duty_type: str
    crew_id: int
    bus_id: Optional[int] = None

    start_time: datetime
    end_time: datetime

    status: str = "PLANNED"


class DutyResponse(BaseModel):
    id: int
    organization_id: int
    duty_name: str
    duty_type: str
    crew_id: int
    bus_id: Optional[int]

    start_time: datetime
    end_time: datetime

    status: str

    class Config:
        from_attributes = True
class GenerateScheduleRequest(BaseModel):
    organization_id: int
    schedule_date: date