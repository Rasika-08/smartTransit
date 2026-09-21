from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# -------------------------
# ORGANIZATION
# -------------------------

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization")
    buses = relationship("Bus", back_populates="organization")
    crew = relationship("Crew", back_populates="organization")
    stops = relationship("Stop", back_populates="organization")
    routes = relationship("Route", back_populates="organization")


# -------------------------
# USERS
# -------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)

    organization = relationship("Organization", back_populates="users")


# -------------------------
# BUSES
# -------------------------

class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    bus_number = Column(String, nullable=False)
    registration_number = Column(String, unique=True, nullable=False)
    capacity = Column(Integer)
    bus_type = Column(String)
    status = Column(String, default="AVAILABLE")

    organization = relationship("Organization", back_populates="buses")


# -------------------------
# CREW
# -------------------------

class Crew(Base):
    __tablename__ = "crew"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    name = Column(String, nullable=False)
    employee_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    phone = Column(String)
    status = Column(String, default="AVAILABLE")

    organization = relationship("Organization", back_populates="crew")


# -------------------------
# STOPS
# -------------------------

class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    organization = relationship("Organization", back_populates="stops")


# -------------------------
# ROUTES
# -------------------------

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    route_number = Column(String, nullable=False)
    route_name = Column(String, nullable=False)
    start_location = Column(String)
    end_location = Column(String)
    distance = Column(Float)
    estimated_duration = Column(Integer)
    status = Column(String, default="ACTIVE")

    organization = relationship("Organization", back_populates="routes")

    route_stops = relationship(
        "RouteStop",
        back_populates="route"
    )


# -------------------------
# ROUTE STOPS
# -------------------------

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)

    route_id = Column(
        Integer,
        ForeignKey("routes.id"),
        nullable=False
    )

    stop_id = Column(
        Integer,
        ForeignKey("stops.id"),
        nullable=False
    )

    sequence_number = Column(Integer, nullable=False)

    route = relationship(
        "Route",
        back_populates="route_stops"
    )
# ==================================================
# TRIP MODEL
# ==================================================

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    route_id = Column(
        Integer,
        ForeignKey("routes.id"),
        nullable=False
    )

    bus_id = Column(
        Integer,
        ForeignKey("buses.id"),
        nullable=True
    )

    driver_id = Column(
        Integer,
        ForeignKey("crew.id"),
        nullable=True
    )

    conductor_id = Column(
        Integer,
        ForeignKey("crew.id"),
        nullable=True
    )

    trip_date = Column(
        DateTime,
        nullable=False
    )

    departure_time = Column(
        DateTime,
        nullable=False
    )

    arrival_time = Column(
        DateTime,
        nullable=False
    )

    status = Column(
        String,
        default="SCHEDULED"
    )

    direction = Column(
        String,
        default="OUTBOUND"
    )
# ==================================================
# SCHEDULE MODEL
# ==================================================

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    trip_id = Column(
        Integer,
        ForeignKey("trips.id"),
        nullable=False
    )

    bus_id = Column(
        Integer,
        ForeignKey("buses.id"),
        nullable=False
    )

    driver_id = Column(
        Integer,
        ForeignKey("crew.id"),
        nullable=False
    )

    conductor_id = Column(
        Integer,
        ForeignKey("crew.id"),
        nullable=False
    )

    scheduled_date = Column(
        DateTime,
        nullable=False
    )

    start_time = Column(
        DateTime,
        nullable=False
    )

    end_time = Column(
        DateTime,
        nullable=False
    )

    duty_type = Column(
        String,
        default="LINKED"
    )

    status = Column(
        String,
        default="SCHEDULED"
    )
# ==================================================
# DUTY MODEL
# ==================================================

class Duty(Base):
    __tablename__ = "duties"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )

    duty_name = Column(
        String,
        nullable=False
    )

    duty_type = Column(
        String,
        nullable=False
    )

    crew_id = Column(
        Integer,
        ForeignKey("crew.id"),
        nullable=False
    )

    bus_id = Column(
        Integer,
        ForeignKey("buses.id"),
        nullable=True
    )

    start_time = Column(
        DateTime,
        nullable=False
    )

    end_time = Column(
        DateTime,
        nullable=False
    )

    status = Column(
        String,
        default="PLANNED"
    )