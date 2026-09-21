from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

import models
import schemas

from scheduler import generate_schedule
from conflict_detector import detect_conflicts
from route_overlap_detector import detect_route_overlaps

from database import engine, SessionLocal, Base


# =========================
# CREATE DATABASE TABLES
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# CREATE FASTAPI APP
# =========================

app = FastAPI(
    title="SmartTransit API",
    description="Bus Scheduling and Route Management System",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# DATABASE CONNECTION
# =========================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================
# ROOT API
# =========================

@app.get("/")
def root():
    return {
        "message": "SmartTransit API is running"
    }


# =========================
# TEST DATABASE
# =========================

@app.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {
            "message": "Database connected successfully"
        }
    except Exception as e:
        return {
            "message": "Database connection failed",
            "error": str(e)
        }


# ==================================================
# ORGANIZATION APIs
# ==================================================


# CREATE ORGANIZATION
@app.post(
    "/organizations",
    response_model=schemas.OrganizationResponse
)
def create_organization(
    organization: schemas.OrganizationCreate,
    db: Session = Depends(get_db)
):

    # Check whether email already exists
    existing_organization = (
        db.query(models.Organization)
        .filter(models.Organization.email == organization.email)
        .first()
    )

    if existing_organization:
        raise HTTPException(
            status_code=400,
            detail="Organization with this email already exists"
        )

    new_organization = models.Organization(
        name=organization.name,
        email=organization.email,
        phone=organization.phone,
        address=organization.address
    )

    db.add(new_organization)
    db.commit()
    db.refresh(new_organization)

    return new_organization


# GET ALL ORGANIZATIONS
@app.get(
    "/organizations",
    response_model=list[schemas.OrganizationResponse]
)
def get_organizations(
    db: Session = Depends(get_db)
):

    organizations = db.query(models.Organization).all()

    return organizations


# GET ORGANIZATION BY ID
@app.get(
    "/organizations/{organization_id}",
    response_model=schemas.OrganizationResponse
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):

    organization = (
        db.query(models.Organization)
        .filter(models.Organization.id == organization_id)
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    return organization


# ==================================================
# BUS APIs
# ==================================================


# CREATE BUS
@app.post(
    "/buses",
    response_model=schemas.BusResponse
)
def create_bus(
    bus: schemas.BusCreate,
    db: Session = Depends(get_db)
):

    # Check whether organization exists
    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == bus.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    # Check duplicate registration number
    existing_bus = (
        db.query(models.Bus)
        .filter(
            models.Bus.registration_number
            == bus.registration_number
        )
        .first()
    )

    if existing_bus:
        raise HTTPException(
            status_code=400,
            detail="Bus with this registration number already exists"
        )

    new_bus = models.Bus(
        organization_id=bus.organization_id,
        bus_number=bus.bus_number,
        registration_number=bus.registration_number,
        capacity=bus.capacity,
        bus_type=bus.bus_type,
        status=bus.status
    )

    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)

    return new_bus


# GET ALL BUSES
@app.get(
    "/buses",
    response_model=list[schemas.BusResponse]
)
def get_buses(
    db: Session = Depends(get_db)
):

    buses = db.query(models.Bus).all()

    return buses


# GET BUS BY ID
@app.get(
    "/buses/{bus_id}",
    response_model=schemas.BusResponse
)
def get_bus(
    bus_id: int,
    db: Session = Depends(get_db)
):

    bus = (
        db.query(models.Bus)
        .filter(models.Bus.id == bus_id)
        .first()
    )

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    return bus


# DELETE BUS
@app.delete("/buses/{bus_id}")
def delete_bus(
    bus_id: int,
    db: Session = Depends(get_db)
):

    bus = (
        db.query(models.Bus)
        .filter(models.Bus.id == bus_id)
        .first()
    )

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    db.delete(bus)
    db.commit()

    return {
        "message": "Bus deleted successfully"
    }
# ==================================================
# CREW APIs
# ==================================================


# CREATE CREW
@app.post(
    "/crew",
    response_model=schemas.CrewResponse
)
def create_crew(
    crew: schemas.CrewCreate,
    db: Session = Depends(get_db)
):

    # Check whether organization exists
    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == crew.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    # Check duplicate employee ID
    existing_crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.employee_id == crew.employee_id
        )
        .first()
    )

    if existing_crew:
        raise HTTPException(
            status_code=400,
            detail="Crew member with this employee ID already exists"
        )

    new_crew = models.Crew(
        organization_id=crew.organization_id,
        name=crew.name,
        employee_id=crew.employee_id,
        role=crew.role,
        phone=crew.phone,
        status=crew.status
    )

    db.add(new_crew)
    db.commit()
    db.refresh(new_crew)

    return new_crew


# GET ALL CREW
@app.get(
    "/crew",
    response_model=list[schemas.CrewResponse]
)
def get_crew(
    db: Session = Depends(get_db)
):

    crew = db.query(models.Crew).all()

    return crew


# GET CREW BY ID
@app.get(
    "/crew/{crew_id}",
    response_model=schemas.CrewResponse
)
def get_crew_member(
    crew_id: int,
    db: Session = Depends(get_db)
):

    crew = (
        db.query(models.Crew)
        .filter(models.Crew.id == crew_id)
        .first()
    )

    if not crew:
        raise HTTPException(
            status_code=404,
            detail="Crew member not found"
        )

    return crew


# DELETE CREW
@app.delete("/crew/{crew_id}")
def delete_crew(
    crew_id: int,
    db: Session = Depends(get_db)
):

    crew = (
        db.query(models.Crew)
        .filter(models.Crew.id == crew_id)
        .first()
    )

    if not crew:
        raise HTTPException(
            status_code=404,
            detail="Crew member not found"
        )

    db.delete(crew)
    db.commit()

    return {
        "message": "Crew member deleted successfully"
    }
# ==================================================
# STOP APIs
# ==================================================


# CREATE STOP
@app.post(
    "/stops",
    response_model=schemas.StopResponse
)
def create_stop(
    stop: schemas.StopCreate,
    db: Session = Depends(get_db)
):

    # Check whether organization exists
    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == stop.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    new_stop = models.Stop(
        organization_id=stop.organization_id,
        name=stop.name,
        latitude=stop.latitude,
        longitude=stop.longitude
    )

    db.add(new_stop)
    db.commit()
    db.refresh(new_stop)

    return new_stop


# GET ALL STOPS
@app.get(
    "/stops",
    response_model=list[schemas.StopResponse]
)
def get_stops(
    db: Session = Depends(get_db)
):

    stops = db.query(models.Stop).all()

    return stops


# GET STOP BY ID
@app.get(
    "/stops/{stop_id}",
    response_model=schemas.StopResponse
)
def get_stop(
    stop_id: int,
    db: Session = Depends(get_db)
):

    stop = (
        db.query(models.Stop)
        .filter(models.Stop.id == stop_id)
        .first()
    )

    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Stop not found"
        )

    return stop


# DELETE STOP
@app.delete("/stops/{stop_id}")
def delete_stop(
    stop_id: int,
    db: Session = Depends(get_db)
):

    stop = (
        db.query(models.Stop)
        .filter(models.Stop.id == stop_id)
        .first()
    )

    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Stop not found"
        )

    db.delete(stop)
    db.commit()

    return {
        "message": "Stop deleted successfully"
    }
# ==================================================
# ROUTE APIs
# ==================================================


# CREATE ROUTE
@app.post(
    "/routes",
    response_model=schemas.RouteResponse
)
def create_route(
    route: schemas.RouteCreate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------
    # 1. Check organization
    # ------------------------------------------

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == route.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )


    # ------------------------------------------
    # 2. Check duplicate route number
    # ------------------------------------------

    existing_route = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id == route.organization_id,
            models.Route.route_number == route.route_number
        )
        .first()
    )

    if existing_route:
        raise HTTPException(
            status_code=400,
            detail="Route with this route number already exists"
        )


    # ------------------------------------------
    # 3. Check that at least two stops exist
    # ------------------------------------------

    if len(route.stop_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="A route must contain at least two stops"
        )


    # ------------------------------------------
    # 4. Check for duplicate stops
    # ------------------------------------------

    if len(route.stop_ids) != len(set(route.stop_ids)):
        raise HTTPException(
            status_code=400,
            detail="A route cannot contain the same stop more than once"
        )


    # ------------------------------------------
    # 5. Check all stops
    # ------------------------------------------

    stops = (
        db.query(models.Stop)
        .filter(
            models.Stop.id.in_(route.stop_ids)
        )
        .all()
    )

    # Check whether all requested stops exist
    if len(stops) != len(route.stop_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more stops were not found"
        )


    # ------------------------------------------
    # 6. Check stop organization
    # ------------------------------------------

    for stop in stops:

        if stop.organization_id != route.organization_id:
            raise HTTPException(
                status_code=400,
                detail=f"Stop {stop.id} does not belong to this organization"
            )


    # ------------------------------------------
    # 7. Create route
    # ------------------------------------------

    new_route = models.Route(
        organization_id=route.organization_id,
        route_number=route.route_number,
        route_name=route.route_name,
        start_location=route.start_location,
        end_location=route.end_location,
        distance=route.distance,
        estimated_duration=route.estimated_duration,
        status=route.status
    )

    db.add(new_route)
    db.commit()
    db.refresh(new_route)


    # ------------------------------------------
    # 8. Add stops to route
    # ------------------------------------------

    for sequence, stop_id in enumerate(route.stop_ids, start=1):

        route_stop = models.RouteStop(
            route_id=new_route.id,
            stop_id=stop_id,
            sequence_number=sequence
        )

        db.add(route_stop)


    db.commit()
    db.refresh(new_route)

    return new_route


# ==================================================
# GET ALL ROUTES
# ==================================================

@app.get(
    "/routes",
    response_model=list[schemas.RouteResponse]
)
def get_routes(
    db: Session = Depends(get_db)
):

    routes = db.query(models.Route).all()

    return routes


# ==================================================
# GET ROUTE BY ID
# ==================================================

@app.get(
    "/routes/{route_id}",
    response_model=schemas.RouteResponse
)
def get_route(
    route_id: int,
    db: Session = Depends(get_db)
):

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == route_id
        )
        .first()
    )

    if not route:
        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    return route


# ==================================================
# DELETE ROUTE
# ==================================================

@app.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db)
):

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == route_id
        )
        .first()
    )

    if not route:
        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )


    # Delete route stops first
    db.query(models.RouteStop).filter(
        models.RouteStop.route_id == route_id
    ).delete()


    # Delete route
    db.delete(route)

    db.commit()

    return {
        "message": "Route deleted successfully"
    }
# ==================================================
# TRIP APIs
# ==================================================


# CREATE TRIP
@app.post(
    "/trips",
    response_model=schemas.TripResponse
)
def create_trip(
    trip: schemas.TripCreate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------
    # 1. Check organization
    # ------------------------------------------

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == trip.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )


    # ------------------------------------------
    # 2. Check route
    # ------------------------------------------

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == trip.route_id
        )
        .first()
    )

    if not route:
        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )


    # ------------------------------------------
    # 3. Check route organization
    # ------------------------------------------

    if route.organization_id != trip.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Route does not belong to this organization"
        )


    # ------------------------------------------
    # 4. Validate time
    # ------------------------------------------

    if trip.arrival_time <= trip.departure_time:
        raise HTTPException(
            status_code=400,
            detail="Arrival time must be after departure time"
        )


    # ------------------------------------------
    # 5. Check bus if provided
    # ------------------------------------------

    if trip.bus_id is not None:

        bus = (
            db.query(models.Bus)
            .filter(
                models.Bus.id == trip.bus_id
            )
            .first()
        )

        if not bus:
            raise HTTPException(
                status_code=404,
                detail="Bus not found"
            )

        if bus.organization_id != trip.organization_id:
            raise HTTPException(
                status_code=400,
                detail="Bus does not belong to this organization"
            )


    # ------------------------------------------
    # 6. Check driver if provided
    # ------------------------------------------

    if trip.driver_id is not None:

        driver = (
            db.query(models.Crew)
            .filter(
                models.Crew.id == trip.driver_id
            )
            .first()
        )

        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )

        if driver.organization_id != trip.organization_id:
            raise HTTPException(
                status_code=400,
                detail="Driver does not belong to this organization"
            )

        if driver.role != "DRIVER":
            raise HTTPException(
                status_code=400,
                detail="Selected crew member is not a driver"
            )


    # ------------------------------------------
    # 7. Check conductor if provided
    # ------------------------------------------

    if trip.conductor_id is not None:

        conductor = (
            db.query(models.Crew)
            .filter(
                models.Crew.id == trip.conductor_id
            )
            .first()
        )

        if not conductor:
            raise HTTPException(
                status_code=404,
                detail="Conductor not found"
            )

        if conductor.organization_id != trip.organization_id:
            raise HTTPException(
                status_code=400,
                detail="Conductor does not belong to this organization"
            )

        if conductor.role != "CONDUCTOR":
            raise HTTPException(
                status_code=400,
                detail="Selected crew member is not a conductor"
            )


    # ------------------------------------------
    # 8. Create trip
    # ------------------------------------------

    new_trip = models.Trip(
        organization_id=trip.organization_id,
        route_id=trip.route_id,
        bus_id=trip.bus_id,
        driver_id=trip.driver_id,
        conductor_id=trip.conductor_id,
        trip_date=trip.trip_date,
        departure_time=trip.departure_time,
        arrival_time=trip.arrival_time,
        status=trip.status,
        direction=trip.direction
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    return new_trip


# ==================================================
# GET ALL TRIPS
# ==================================================

@app.get(
    "/trips",
    response_model=list[schemas.TripResponse]
)
def get_trips(
    db: Session = Depends(get_db)
):

    trips = db.query(models.Trip).all()

    return trips


# ==================================================
# GET TRIP BY ID
# ==================================================

@app.get(
    "/trips/{trip_id}",
    response_model=schemas.TripResponse
)
def get_trip(
    trip_id: int,
    db: Session = Depends(get_db)
):

    trip = (
        db.query(models.Trip)
        .filter(
            models.Trip.id == trip_id
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    return trip


# ==================================================
# DELETE TRIP
# ==================================================

@app.delete("/trips/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db)
):

    trip = (
        db.query(models.Trip)
        .filter(
            models.Trip.id == trip_id
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    db.delete(trip)
    db.commit()

    return {
        "message": "Trip deleted successfully"
    }
# ==================================================
# SCHEDULE APIs
# ==================================================


# CREATE SCHEDULE
@app.post(
    "/schedules",
    response_model=schemas.ScheduleResponse
)
def create_schedule(
    schedule: schemas.ScheduleCreate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------
    # 1. Validate time
    # ------------------------------------------

    if schedule.end_time <= schedule.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )


    # ------------------------------------------
    # 2. Check organization
    # ------------------------------------------

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == schedule.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )


    # ------------------------------------------
    # 3. Check trip
    # ------------------------------------------

    trip = (
        db.query(models.Trip)
        .filter(
            models.Trip.id == schedule.trip_id
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )


    if trip.organization_id != schedule.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Trip does not belong to this organization"
        )


    # ------------------------------------------
    # 4. Check bus
    # ------------------------------------------

    bus = (
        db.query(models.Bus)
        .filter(
            models.Bus.id == schedule.bus_id
        )
        .first()
    )

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )


    if bus.organization_id != schedule.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Bus does not belong to this organization"
        )


    # ------------------------------------------
    # 5. Check driver
    # ------------------------------------------

    driver = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == schedule.driver_id
        )
        .first()
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver not found"
        )


    if driver.organization_id != schedule.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Driver does not belong to this organization"
        )


    if driver.role != "DRIVER":
        raise HTTPException(
            status_code=400,
            detail="Selected crew member is not a driver"
        )


    # ------------------------------------------
    # 6. Check conductor
    # ------------------------------------------

    conductor = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == schedule.conductor_id
        )
        .first()
    )

    if not conductor:
        raise HTTPException(
            status_code=404,
            detail="Conductor not found"
        )


    if conductor.organization_id != schedule.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Conductor does not belong to this organization"
        )


    if conductor.role != "CONDUCTOR":
        raise HTTPException(
            status_code=400,
            detail="Selected crew member is not a conductor"
        )


    # ==================================================
    # CONFLICT DETECTION
    # ==================================================


    # ------------------------------------------
    # 7. Bus conflict
    # ------------------------------------------

    bus_conflict = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.bus_id == schedule.bus_id,
            models.Schedule.scheduled_date == schedule.scheduled_date,
            models.Schedule.start_time < schedule.end_time,
            models.Schedule.end_time > schedule.start_time,
            models.Schedule.status != "CANCELLED"
        )
        .first()
    )

    if bus_conflict:
        raise HTTPException(
            status_code=409,
            detail="Bus is already assigned to another schedule during this time"
        )


    # ------------------------------------------
    # 8. Driver conflict
    # ------------------------------------------

    driver_conflict = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.driver_id == schedule.driver_id,
            models.Schedule.scheduled_date == schedule.scheduled_date,
            models.Schedule.start_time < schedule.end_time,
            models.Schedule.end_time > schedule.start_time,
            models.Schedule.status != "CANCELLED"
        )
        .first()
    )

    if driver_conflict:
        raise HTTPException(
            status_code=409,
            detail="Driver is already assigned to another schedule during this time"
        )


    # ------------------------------------------
    # 9. Conductor conflict
    # ------------------------------------------

    conductor_conflict = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.conductor_id == schedule.conductor_id,
            models.Schedule.scheduled_date == schedule.scheduled_date,
            models.Schedule.start_time < schedule.end_time,
            models.Schedule.end_time > schedule.start_time,
            models.Schedule.status != "CANCELLED"
        )
        .first()
    )

    if conductor_conflict:
        raise HTTPException(
            status_code=409,
            detail="Conductor is already assigned to another schedule during this time"
        )


    # ------------------------------------------
    # 10. Create schedule
    # ------------------------------------------

    new_schedule = models.Schedule(
        organization_id=schedule.organization_id,
        trip_id=schedule.trip_id,
        bus_id=schedule.bus_id,
        driver_id=schedule.driver_id,
        conductor_id=schedule.conductor_id,
        scheduled_date=schedule.scheduled_date,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        duty_type=schedule.duty_type,
        status=schedule.status
    )

    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)

    return new_schedule


# ==================================================
# GET ALL SCHEDULES
# ==================================================

@app.get(
    "/schedules",
    response_model=list[schemas.ScheduleResponse]
)
def get_schedules(
    db: Session = Depends(get_db)
):

    schedules = (
        db.query(models.Schedule)
        .all()
    )

    return schedules


# ==================================================
# GET SCHEDULE BY ID
# ==================================================

@app.get(
    "/schedules/{schedule_id}",
    response_model=schemas.ScheduleResponse
)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):

    schedule = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.id == schedule_id
        )
        .first()
    )

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found"
        )

    return schedule


# ==================================================
# DELETE SCHEDULE
# ==================================================

@app.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):

    schedule = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.id == schedule_id
        )
        .first()
    )

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found"
        )

    db.delete(schedule)
    db.commit()

    return {
        "message": "Schedule deleted successfully"
    }
# ==================================================
# DUTY APIs
# ==================================================


# CREATE DUTY
@app.post(
    "/duties",
    response_model=schemas.DutyResponse
)
def create_duty(
    duty: schemas.DutyCreate,
    db: Session = Depends(get_db)
):
    # 1. Validate time
    if duty.end_time <= duty.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    # 2. Validate duty type
    allowed_types = ["LINKED", "UNLINKED"]

    if duty.duty_type.upper() not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Duty type must be LINKED or UNLINKED"
        )

    # 3. Check organization
    organization = (
        db.query(models.Organization)
        .filter(models.Organization.id == duty.organization_id)
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    # 4. Check crew
    crew = (
        db.query(models.Crew)
        .filter(models.Crew.id == duty.crew_id)
        .first()
    )

    if not crew:
        raise HTTPException(
            status_code=404,
            detail="Crew member not found"
        )

    if crew.organization_id != duty.organization_id:
        raise HTTPException(
            status_code=400,
            detail="Crew member does not belong to this organization"
        )

    # 5. Check bus
    if duty.bus_id is not None:
        bus = (
            db.query(models.Bus)
            .filter(models.Bus.id == duty.bus_id)
            .first()
        )

        if not bus:
            raise HTTPException(
                status_code=404,
                detail="Bus not found"
            )

        if bus.organization_id != duty.organization_id:
            raise HTTPException(
                status_code=400,
                detail="Bus does not belong to this organization"
            )

    # 6. Crew conflict + 30-minute rest period
    MIN_REST_MINUTES = 30
    minimum_rest = timedelta(minutes=MIN_REST_MINUTES)

    crew_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.crew_id == duty.crew_id,
            models.Duty.status != "CANCELLED"
        )
        .all()
    )

    for existing_duty in crew_duties:

        # Direct overlap
        if (
            existing_duty.start_time < duty.end_time
            and existing_duty.end_time > duty.start_time
        ):
            raise HTTPException(
                status_code=409,
                detail="Crew member already has another duty during this time"
            )

        # New duty starts less than 30 minutes after old duty
        if (
            duty.start_time >= existing_duty.end_time
            and duty.start_time - existing_duty.end_time < minimum_rest
        ):
            raise HTTPException(
                status_code=409,
                detail="Crew member does not have the required 30-minute rest period"
            )

        # New duty ends less than 30 minutes before next duty
        if (
            existing_duty.start_time >= duty.end_time
            and existing_duty.start_time - duty.end_time < minimum_rest
        ):
            raise HTTPException(
                status_code=409,
                detail="Crew member does not have the required 30-minute rest period"
            )

    # 7. Linked duty rule
    if duty.duty_type.upper() == "LINKED":

        if duty.bus_id is None:
            raise HTTPException(
                status_code=400,
                detail="Linked duty requires a bus"
            )

        linked_conflict = (
            db.query(models.Duty)
            .filter(
                models.Duty.crew_id == duty.crew_id,
                models.Duty.duty_type == "LINKED",
                models.Duty.start_time < duty.end_time,
                models.Duty.end_time > duty.start_time,
                models.Duty.bus_id != duty.bus_id,
                models.Duty.status != "CANCELLED"
            )
            .first()
        )

        if linked_conflict:
            raise HTTPException(
                status_code=409,
                detail="Crew member is already linked to another bus during this time"
            )

    # 8. Bus conflict detection
    if duty.bus_id is not None:

        bus_conflict = (
            db.query(models.Duty)
            .filter(
                models.Duty.bus_id == duty.bus_id,
                models.Duty.start_time < duty.end_time,
                models.Duty.end_time > duty.start_time,
                models.Duty.status != "CANCELLED"
            )
            .first()
        )

        if bus_conflict:
            raise HTTPException(
                status_code=409,
                detail="Bus is already assigned to another duty during this time"
            )

    # 9. Create duty
    new_duty = models.Duty(
        organization_id=duty.organization_id,
        duty_name=duty.duty_name,
        duty_type=duty.duty_type.upper(),
        crew_id=duty.crew_id,
        bus_id=duty.bus_id,
        start_time=duty.start_time,
        end_time=duty.end_time,
        status=duty.status
    )

    db.add(new_duty)
    db.commit()
    db.refresh(new_duty)

    return new_duty


# ==================================================
# GET ALL DUTIES
# ==================================================

@app.get(
    "/duties",
    response_model=list[schemas.DutyResponse]
)
def get_duties(
    db: Session = Depends(get_db)
):

    return db.query(models.Duty).all()


# ==================================================
# GET DUTY BY ID
# ==================================================

@app.get(
    "/duties/{duty_id}",
    response_model=schemas.DutyResponse
)
def get_duty(
    duty_id: int,
    db: Session = Depends(get_db)
):

    duty = (
        db.query(models.Duty)
        .filter(
            models.Duty.id == duty_id
        )
        .first()
    )

    if not duty:
        raise HTTPException(
            status_code=404,
            detail="Duty not found"
        )

    return duty


# ==================================================
# DELETE DUTY
# ==================================================

@app.delete("/duties/{duty_id}")
def delete_duty(
    duty_id: int,
    db: Session = Depends(get_db)
):

    duty = (
        db.query(models.Duty)
        .filter(
            models.Duty.id == duty_id
        )
        .first()
    )

    if not duty:
        raise HTTPException(
            status_code=404,
            detail="Duty not found"
        )

    db.delete(duty)
    db.commit()

    return {
        "message": "Duty deleted successfully"
    }
# ==================================================
# AUTOMATED SCHEDULING API
# ==================================================


@app.post("/generate-schedule")
def generate_automated_schedule(
    request: schemas.GenerateScheduleRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------
    # 1. Check organization
    # --------------------------------------------------

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == request.organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    # --------------------------------------------------
    # 2. Get trips for selected date
    # --------------------------------------------------

    trips = (
        db.query(models.Trip)
        .filter(
            models.Trip.organization_id == request.organization_id,
            models.Trip.trip_date >= datetime.combine(
                request.schedule_date,
                datetime.min.time()
            ),
            models.Trip.trip_date < datetime.combine(
                request.schedule_date,
                datetime.min.time()
            ) + timedelta(days=1)
        )
        .all()
    )

    # --------------------------------------------------
    # 3. Remove trips that are already scheduled
    # --------------------------------------------------

    scheduled_trip_ids = {
        schedule.trip_id
        for schedule in (
            db.query(models.Schedule)
            .filter(
                models.Schedule.organization_id
                == request.organization_id
            )
            .all()
        )
    }

    unscheduled_trips = [
        trip
        for trip in trips
        if trip.id not in scheduled_trip_ids
    ]

    if not unscheduled_trips:

        return {
            "success": False,
            "message": "No unscheduled trips found for this date",
            "assignments": []
        }

    # --------------------------------------------------
    # 4. Get available buses
    # --------------------------------------------------

    buses = (
        db.query(models.Bus)
        .filter(
            models.Bus.organization_id
            == request.organization_id,
            models.Bus.status == "AVAILABLE"
        )
        .all()
    )

    # --------------------------------------------------
    # 5. Get available drivers
    # --------------------------------------------------

    drivers = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == request.organization_id,
            models.Crew.role == "DRIVER",
            models.Crew.status == "AVAILABLE"
        )
        .all()
    )

    # --------------------------------------------------
    # 6. Get available conductors
    # --------------------------------------------------

    conductors = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == request.organization_id,
            models.Crew.role == "CONDUCTOR",
            models.Crew.status == "AVAILABLE"
        )
        .all()
    )

    if not buses:
        raise HTTPException(
            status_code=400,
            detail="No available buses found"
        )

    if not drivers:
        raise HTTPException(
            status_code=400,
            detail="No available drivers found"
        )

    if not conductors:
        raise HTTPException(
            status_code=400,
            detail="No available conductors found"
        )

    # --------------------------------------------------
    # 7. Get existing schedules
    # --------------------------------------------------

    existing_schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == request.organization_id
        )
        .all()
    )

    # --------------------------------------------------
    # 8. Get existing duties
    # --------------------------------------------------

    existing_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == request.organization_id,
            models.Duty.status != "CANCELLED"
        )
        .all()
    )

    # --------------------------------------------------
    # 9. Run OR-Tools scheduling engine
    # --------------------------------------------------

    result = generate_schedule(
        trips=unscheduled_trips,
        buses=buses,
        drivers=drivers,
        conductors=conductors,
        existing_schedules=existing_schedules,
        existing_duties=existing_duties
    )

    # --------------------------------------------------
    # 10. If scheduling failed
    # --------------------------------------------------

    if not result["success"]:
        return result

    # --------------------------------------------------
    # 11. Save generated schedules
    # --------------------------------------------------

    created_schedules = []

    for assignment in result["assignments"]:

        new_schedule = models.Schedule(
            organization_id=request.organization_id,
            trip_id=assignment["trip_id"],
            bus_id=assignment["bus_id"],
            driver_id=assignment["driver_id"],
            conductor_id=assignment["conductor_id"],
            scheduled_date=datetime.combine(
                request.schedule_date,
                datetime.min.time()
            ),
            start_time=assignment["start_time"],
            end_time=assignment["end_time"],
            duty_type="AUTO",
            status="SCHEDULED"
        )

        db.add(new_schedule)

        created_schedules.append(
            {
                "trip_id": assignment["trip_id"],
                "bus_id": assignment["bus_id"],
                "driver_id": assignment["driver_id"],
                "conductor_id": assignment["conductor_id"],
                "start_time": assignment["start_time"],
                "end_time": assignment["end_time"]
            }
        )

    db.commit()

    # --------------------------------------------------
    # 12. Return result
    # --------------------------------------------------

    return {
        "success": True,
        "message": "Automated schedule generated successfully",
        "schedule_date": request.schedule_date,
        "total_trips_scheduled": len(created_schedules),
        "assignments": created_schedules
    }
# ==================================================
# CONFLICT DETECTION API
# ==================================================

@app.get("/conflicts/{organization_id}")
def get_conflicts(
    organization_id: int,
    db: Session = Depends(get_db)
):
    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == organization_id
        )
        .first()
    )

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id == organization_id,
            models.Schedule.status != "CANCELLED"
        )
        .all()
    )

    duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id == organization_id,
            models.Duty.status != "CANCELLED"
        )
        .all()
    )

    conflicts = detect_conflicts(
        schedules=schedules,
        duties=duties
    )

    return {
        "success": True,
        "organization_id": organization_id,
        "total_conflicts": len(conflicts),
        "conflicts": conflicts
    }
@app.get("/routes/{route_id}/overlaps")
def get_route_overlaps(route_id: int, db: Session = Depends(get_db)):

    target_route = db.query(models.Route).filter(
        models.Route.id == route_id
    ).first()

    if not target_route:
        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    routes = db.query(models.Route).filter(
        models.Route.organization_id == target_route.organization_id,
        models.Route.status == "ACTIVE"
    ).all()

    stops = db.query(models.Stop).filter(
        models.Stop.organization_id == target_route.organization_id
    ).all()

    stop_names = {
        stop.id: stop.name
        for stop in stops
    }

    overlaps = detect_route_overlaps(
        target_route,
        routes,
        stop_names
    )

    return {
        "success": True,
        "route_id": target_route.id,
        "route_number": target_route.route_number,
        "route_name": target_route.route_name,
        "total_overlaps": len(overlaps),
        "overlaps": overlaps
    }
@app.get("/routes/{route_id}/map-data")
def get_route_map_data(route_id: int, db: Session = Depends(get_db)):

    route = db.query(models.Route).filter(
        models.Route.id == route_id
    ).first()

    if not route:
        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    route_stops = sorted(
        route.route_stops,
        key=lambda x: x.sequence_number
    )

    map_stops = []

    for route_stop in route_stops:

        stop = db.query(models.Stop).filter(
            models.Stop.id == route_stop.stop_id,
            models.Stop.organization_id == route.organization_id
        ).first()

        if stop:
            map_stops.append({
                "stop_id": stop.id,
                "name": stop.name,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "sequence_number": route_stop.sequence_number
            })

    coordinates = [
        [stop["latitude"], stop["longitude"]]
        for stop in map_stops
    ]

    return {
        "success": True,
        "route_id": route.id,
        "route_number": route.route_number,
        "route_name": route.route_name,
        "start_location": route.start_location,
        "end_location": route.end_location,
        "stops": map_stops,
        "coordinates": coordinates
    }
@app.get("/dashboard/{organization_id}")
def get_dashboard(organization_id: int, db: Session = Depends(get_db)):

    # Check organization
    organization = db.query(models.Organization).filter(
        models.Organization.id == organization_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    # -------------------------
    # BUS STATISTICS
    # -------------------------

    total_buses = db.query(models.Bus).filter(
        models.Bus.organization_id == organization_id
    ).count()

    available_buses = db.query(models.Bus).filter(
        models.Bus.organization_id == organization_id,
        models.Bus.status == "AVAILABLE"
    ).count()

    # -------------------------
    # CREW STATISTICS
    # -------------------------

    total_crew = db.query(models.Crew).filter(
        models.Crew.organization_id == organization_id
    ).count()

    available_crew = db.query(models.Crew).filter(
        models.Crew.organization_id == organization_id,
        models.Crew.status == "AVAILABLE"
    ).count()

    # -------------------------
    # ROUTE STATISTICS
    # -------------------------

    total_routes = db.query(models.Route).filter(
        models.Route.organization_id == organization_id
    ).count()

    active_routes = db.query(models.Route).filter(
        models.Route.organization_id == organization_id,
        models.Route.status == "ACTIVE"
    ).count()

    # -------------------------
    # TRIP STATISTICS
    # -------------------------

    total_trips = db.query(models.Trip).filter(
        models.Trip.organization_id == organization_id
    ).count()

    scheduled_trips = db.query(models.Trip).filter(
        models.Trip.organization_id == organization_id,
        models.Trip.status == "SCHEDULED"
    ).count()

    # -------------------------
    # SCHEDULE STATISTICS
    # -------------------------

    total_schedules = db.query(models.Schedule).filter(
        models.Schedule.organization_id == organization_id
    ).count()

    automatic_schedules = db.query(models.Schedule).filter(
        models.Schedule.organization_id == organization_id,
        models.Schedule.duty_type == "AUTO"
    ).count()

    manual_schedules = total_schedules - automatic_schedules

    # -------------------------
    # DUTY STATISTICS
    # -------------------------

    total_duties = db.query(models.Duty).filter(
        models.Duty.organization_id == organization_id
    ).count()

    linked_duties = db.query(models.Duty).filter(
        models.Duty.organization_id == organization_id,
        models.Duty.duty_type == "LINKED"
    ).count()

    unlinked_duties = db.query(models.Duty).filter(
        models.Duty.organization_id == organization_id,
        models.Duty.duty_type == "UNLINKED"
    ).count()

    # -------------------------
    # CONFLICT STATISTICS
    # -------------------------

    schedules = db.query(models.Schedule).filter(
        models.Schedule.organization_id == organization_id
    ).all()

    duties = db.query(models.Duty).filter(
        models.Duty.organization_id == organization_id
    ).all()

    conflicts = detect_conflicts(schedules, duties)

    total_conflicts = len(conflicts)

    # -------------------------
    # ROUTE OVERLAP STATISTICS
    # -------------------------

    routes = db.query(models.Route).filter(
        models.Route.organization_id == organization_id
    ).all()

    route_overlap_pairs = 0

    for i in range(len(routes)):
        route1_stop_ids = {
            rs.stop_id
            for rs in routes[i].route_stops
        }

        for j in range(i + 1, len(routes)):
            route2_stop_ids = {
                rs.stop_id
                for rs in routes[j].route_stops
            }

            common_stops = route1_stop_ids.intersection(
                route2_stop_ids
            )

            if len(common_stops) >= 2:
                route_overlap_pairs += 1

    # -------------------------
    # RESPONSE
    # -------------------------

    return {
        "success": True,
        "organization_id": organization_id,

        "buses": {
            "total": total_buses,
            "available": available_buses
        },

        "crew": {
            "total": total_crew,
            "available": available_crew
        },

        "routes": {
            "total": total_routes,
            "active": active_routes
        },

        "trips": {
            "total": total_trips,
            "scheduled": scheduled_trips
        },

        "schedules": {
            "total": total_schedules,
            "automatic": automatic_schedules,
            "manual": manual_schedules
        },

        "duties": {
            "total": total_duties,
            "linked": linked_duties,
            "unlinked": unlinked_duties
        },

        "conflicts": {
            "total": total_conflicts
        },

        "route_overlaps": {
            "total": route_overlap_pairs
        }
    }