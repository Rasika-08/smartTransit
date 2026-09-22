from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import text

from datetime import timedelta, datetime

import models
import schemas

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

from scheduler import generate_schedule
from conflict_detector import detect_conflicts
from route_overlap_detector import detect_route_overlaps

from database import engine, SessionLocal, Base


# ==================================================
# CREATE DATABASE TABLES
# ==================================================

Base.metadata.create_all(bind=engine)


# ==================================================
# CREATE FASTAPI APP
# ==================================================

app = FastAPI(
    title="SmartTransit API",
    description="Bus Scheduling and Route Management System",
    version="1.0.0"
)


# ==================================================
# CORS
# ==================================================

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


# ==================================================
# AUTHENTICATION
# ==================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==================================================
# CURRENT USER
# ==================================================

def get_authenticated_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# ==================================================
# ROOT API
# ==================================================

@app.get("/")
def root():

    return {
        "message": "SmartTransit API is running"
    }


# ==================================================
# TEST DATABASE
# ==================================================

@app.get("/test-db")
def test_database(
    db: Session = Depends(get_db)
):

    try:

        db.execute(text("SELECT 1"))

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
# This remains public because a new organization
# must be able to register before users exist.

@app.post(
    "/organizations",
    response_model=schemas.OrganizationResponse
)
def create_organization(
    organization: schemas.OrganizationCreate,
    db: Session = Depends(get_db)
):

    existing_organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.email == organization.email
        )
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
#
# Protected.
# A user can only see their own organization.

@app.get(
    "/organizations",
    response_model=list[schemas.OrganizationResponse]
)
def get_organizations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    organizations = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == current_user.organization_id
        )
        .all()
    )

    return organizations


# GET ORGANIZATION BY ID

@app.get(
    "/organizations/{organization_id}",
    response_model=schemas.OrganizationResponse
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if bus.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id == current_user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

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
        organization_id=current_user.organization_id,
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

@app.get("/buses")
def get_buses(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    buses = (
        db.query(models.Bus)
        .filter(
            models.Bus.organization_id
            == current_user.organization_id
        )
        .all()
    )

    return buses


# GET BUS BY ID

@app.get(
    "/buses/{bus_id}",
    response_model=schemas.BusResponse
)
def get_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    bus = (
        db.query(models.Bus)
        .filter(
            models.Bus.id == bus_id,
            models.Bus.organization_id
            == current_user.organization_id
        )
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    bus = (
        db.query(models.Bus)
        .filter(
            models.Bus.id == bus_id,
            models.Bus.organization_id
            == current_user.organization_id
        )
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if crew.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id
            == current_user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    existing_crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.employee_id
            == crew.employee_id
        )
        .first()
    )

    if existing_crew:

        raise HTTPException(
            status_code=400,
            detail="Crew member with this employee ID already exists"
        )

    new_crew = models.Crew(
        organization_id=current_user.organization_id,
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
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == current_user.organization_id
        )
        .all()
    )

    return crew


# GET CREW BY ID

@app.get(
    "/crew/{crew_id}",
    response_model=schemas.CrewResponse
)
def get_crew_member(
    crew_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == crew_id,
            models.Crew.organization_id
            == current_user.organization_id
        )
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == crew_id,
            models.Crew.organization_id
            == current_user.organization_id
        )
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if stop.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id
            == current_user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    new_stop = models.Stop(
        organization_id=current_user.organization_id,
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
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    stops = (
        db.query(models.Stop)
        .filter(
            models.Stop.organization_id
            == current_user.organization_id
        )
        .all()
    )

    return stops


# GET STOP BY ID

@app.get(
    "/stops/{stop_id}",
    response_model=schemas.StopResponse
)
def get_stop(
    stop_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    stop = (
        db.query(models.Stop)
        .filter(
            models.Stop.id == stop_id,
            models.Stop.organization_id
            == current_user.organization_id
        )
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    stop = (
        db.query(models.Stop)
        .filter(
            models.Stop.id == stop_id,
            models.Stop.organization_id
            == current_user.organization_id
        )
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if route.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id
            == current_user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    existing_route = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id
            == current_user.organization_id,
            models.Route.route_number
            == route.route_number
        )
        .first()
    )

    if existing_route:

        raise HTTPException(
            status_code=400,
            detail="Route with this route number already exists"
        )

    if len(route.stop_ids) < 2:

        raise HTTPException(
            status_code=400,
            detail="A route must contain at least two stops"
        )

    if len(route.stop_ids) != len(set(route.stop_ids)):

        raise HTTPException(
            status_code=400,
            detail="A route cannot contain the same stop more than once"
        )

    stops = (
        db.query(models.Stop)
        .filter(
            models.Stop.id.in_(route.stop_ids),
            models.Stop.organization_id
            == current_user.organization_id
        )
        .all()
    )

    if len(stops) != len(route.stop_ids):

        raise HTTPException(
            status_code=404,
            detail="One or more stops were not found"
        )

    new_route = models.Route(
        organization_id=current_user.organization_id,
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

    for sequence, stop_id in enumerate(
        route.stop_ids,
        start=1
    ):

        route_stop = models.RouteStop(
            route_id=new_route.id,
            stop_id=stop_id,
            sequence_number=sequence
        )

        db.add(route_stop)

    db.commit()
    db.refresh(new_route)

    return new_route


# GET ALL ROUTES

@app.get(
    "/routes",
    response_model=list[schemas.RouteResponse]
)
def get_routes(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    routes = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id
            == current_user.organization_id
        )
        .all()
    )

    return routes


# GET ROUTE BY ID

@app.get(
    "/routes/{route_id}",
    response_model=schemas.RouteResponse
)
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == route_id,
            models.Route.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not route:

        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    return route


# DELETE ROUTE

@app.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == route_id,
            models.Route.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not route:

        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    db.query(models.RouteStop).filter(
        models.RouteStop.route_id == route_id
    ).delete()

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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if trip.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id
            == current_user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == trip.route_id,
            models.Route.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not route:

        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    if trip.arrival_time <= trip.departure_time:

        raise HTTPException(
            status_code=400,
            detail="Arrival time must be after departure time"
        )

    if trip.bus_id is not None:

        bus = (
            db.query(models.Bus)
            .filter(
                models.Bus.id == trip.bus_id,
                models.Bus.organization_id
                == current_user.organization_id
            )
            .first()
        )

        if not bus:

            raise HTTPException(
                status_code=404,
                detail="Bus not found"
            )

    if trip.driver_id is not None:

        driver = (
            db.query(models.Crew)
            .filter(
                models.Crew.id == trip.driver_id,
                models.Crew.organization_id
                == current_user.organization_id
            )
            .first()
        )

        if not driver:

            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )

        if driver.role != "DRIVER":

            raise HTTPException(
                status_code=400,
                detail="Selected crew member is not a driver"
            )

    if trip.conductor_id is not None:

        conductor = (
            db.query(models.Crew)
            .filter(
                models.Crew.id == trip.conductor_id,
                models.Crew.organization_id
                == current_user.organization_id
            )
            .first()
        )

        if not conductor:

            raise HTTPException(
                status_code=404,
                detail="Conductor not found"
            )

        if conductor.role != "CONDUCTOR":

            raise HTTPException(
                status_code=400,
                detail="Selected crew member is not a conductor"
            )

    new_trip = models.Trip(
        organization_id=current_user.organization_id,
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


# GET ALL TRIPS

@app.get(
    "/trips",
    response_model=list[schemas.TripResponse]
)
def get_trips(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    trips = (
        db.query(models.Trip)
        .filter(
            models.Trip.organization_id
            == current_user.organization_id
        )
        .all()
    )

    return trips


# GET TRIP BY ID

@app.get(
    "/trips/{trip_id}",
    response_model=schemas.TripResponse
)
def get_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    trip = (
        db.query(models.Trip)
        .filter(
            models.Trip.id == trip_id,
            models.Trip.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not trip:

        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    return trip


# DELETE TRIP

@app.delete("/trips/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    trip = (
        db.query(models.Trip)
        .filter(
            models.Trip.id == trip_id,
            models.Trip.organization_id
            == current_user.organization_id
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if schedule.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    if schedule.end_time <= schedule.start_time:

        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    trip = (
        db.query(models.Trip)
        .filter(
            models.Trip.id == schedule.trip_id,
            models.Trip.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not trip:

        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    bus = (
        db.query(models.Bus)
        .filter(
            models.Bus.id == schedule.bus_id,
            models.Bus.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not bus:

        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    driver = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == schedule.driver_id,
            models.Crew.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not driver:

        raise HTTPException(
            status_code=404,
            detail="Driver not found"
        )

    if driver.role != "DRIVER":

        raise HTTPException(
            status_code=400,
            detail="Selected crew member is not a driver"
        )

    conductor = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == schedule.conductor_id,
            models.Crew.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not conductor:

        raise HTTPException(
            status_code=404,
            detail="Conductor not found"
        )

    if conductor.role != "CONDUCTOR":

        raise HTTPException(
            status_code=400,
            detail="Selected crew member is not a conductor"
        )

    # BUS CONFLICT

    bus_conflict = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id,
            models.Schedule.bus_id == schedule.bus_id,
            models.Schedule.scheduled_date
            == schedule.scheduled_date,
            models.Schedule.start_time
            < schedule.end_time,
            models.Schedule.end_time
            > schedule.start_time,
            models.Schedule.status != "CANCELLED"
        )
        .first()
    )

    if bus_conflict:

        raise HTTPException(
            status_code=409,
            detail="Bus is already assigned to another schedule during this time"
        )

    # DRIVER CONFLICT

    driver_conflict = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id,
            models.Schedule.driver_id == schedule.driver_id,
            models.Schedule.scheduled_date
            == schedule.scheduled_date,
            models.Schedule.start_time
            < schedule.end_time,
            models.Schedule.end_time
            > schedule.start_time,
            models.Schedule.status != "CANCELLED"
        )
        .first()
    )

    if driver_conflict:

        raise HTTPException(
            status_code=409,
            detail="Driver is already assigned to another schedule during this time"
        )

    # CONDUCTOR CONFLICT

    conductor_conflict = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id,
            models.Schedule.conductor_id
            == schedule.conductor_id,
            models.Schedule.scheduled_date
            == schedule.scheduled_date,
            models.Schedule.start_time
            < schedule.end_time,
            models.Schedule.end_time
            > schedule.start_time,
            models.Schedule.status != "CANCELLED"
        )
        .first()
    )

    if conductor_conflict:

        raise HTTPException(
            status_code=409,
            detail="Conductor is already assigned to another schedule during this time"
        )

    new_schedule = models.Schedule(
        organization_id=current_user.organization_id,
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


# GET ALL SCHEDULES

@app.get(
    "/schedules",
    response_model=list[schemas.ScheduleResponse]
)
def get_schedules(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id
        )
        .all()
    )

    return schedules


# GET SCHEDULE BY ID

@app.get(
    "/schedules/{schedule_id}",
    response_model=schemas.ScheduleResponse
)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    schedule = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.id == schedule_id,
            models.Schedule.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not schedule:

        raise HTTPException(
            status_code=404,
            detail="Schedule not found"
        )

    return schedule


# DELETE SCHEDULE

@app.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    schedule = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.id == schedule_id,
            models.Schedule.organization_id
            == current_user.organization_id
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if duty.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot create data for another organization"
        )

    if duty.end_time <= duty.start_time:

        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    allowed_types = [
        "LINKED",
        "UNLINKED"
    ]

    if duty.duty_type.upper() not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail="Duty type must be LINKED or UNLINKED"
        )

    crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.id == duty.crew_id,
            models.Crew.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not crew:

        raise HTTPException(
            status_code=404,
            detail="Crew member not found"
        )

    if duty.bus_id is not None:

        bus = (
            db.query(models.Bus)
            .filter(
                models.Bus.id == duty.bus_id,
                models.Bus.organization_id
                == current_user.organization_id
            )
            .first()
        )

        if not bus:

            raise HTTPException(
                status_code=404,
                detail="Bus not found"
            )

    MIN_REST_MINUTES = 30

    minimum_rest = timedelta(
        minutes=MIN_REST_MINUTES
    )

    crew_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id,
            models.Duty.crew_id == duty.crew_id,
            models.Duty.status != "CANCELLED"
        )
        .all()
    )

    for existing_duty in crew_duties:

        if (
            existing_duty.start_time < duty.end_time
            and existing_duty.end_time > duty.start_time
        ):

            raise HTTPException(
                status_code=409,
                detail="Crew member already has another duty during this time"
            )

        if (
            duty.start_time >= existing_duty.end_time
            and
            duty.start_time - existing_duty.end_time
            < minimum_rest
        ):

            raise HTTPException(
                status_code=409,
                detail="Crew member does not have the required 30-minute rest period"
            )

        if (
            existing_duty.start_time >= duty.end_time
            and
            existing_duty.start_time - duty.end_time
            < minimum_rest
        ):

            raise HTTPException(
                status_code=409,
                detail="Crew member does not have the required 30-minute rest period"
            )

    # LINKED DUTY

    if duty.duty_type.upper() == "LINKED":

        if duty.bus_id is None:

            raise HTTPException(
                status_code=400,
                detail="Linked duty requires a bus"
            )

        linked_conflict = (
            db.query(models.Duty)
            .filter(
                models.Duty.organization_id
                == current_user.organization_id,
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

    # BUS CONFLICT

    if duty.bus_id is not None:

        bus_conflict = (
            db.query(models.Duty)
            .filter(
                models.Duty.organization_id
                == current_user.organization_id,
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

    new_duty = models.Duty(
        organization_id=current_user.organization_id,
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


# GET ALL DUTIES

@app.get(
    "/duties",
    response_model=list[schemas.DutyResponse]
)
def get_duties(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's data"
        )

    return (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id
        )
        .all()
    )


# GET DUTY BY ID

@app.get(
    "/duties/{duty_id}",
    response_model=schemas.DutyResponse
)
def get_duty(
    duty_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    duty = (
        db.query(models.Duty)
        .filter(
            models.Duty.id == duty_id,
            models.Duty.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not duty:

        raise HTTPException(
            status_code=404,
            detail="Duty not found"
        )

    return duty


# DELETE DUTY

@app.delete("/duties/{duty_id}")
def delete_duty(
    duty_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    duty = (
        db.query(models.Duty)
        .filter(
            models.Duty.id == duty_id,
            models.Duty.organization_id
            == current_user.organization_id
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if request.organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot generate schedules for another organization"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id
            == current_user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    start_of_day = datetime.combine(
        request.schedule_date,
        datetime.min.time()
    )

    end_of_day = start_of_day + timedelta(days=1)

    trips = (
        db.query(models.Trip)
        .filter(
            models.Trip.organization_id
            == current_user.organization_id,
            models.Trip.trip_date >= start_of_day,
            models.Trip.trip_date < end_of_day
        )
        .all()
    )

    scheduled_trip_ids = {
        schedule.trip_id
        for schedule in (
            db.query(models.Schedule)
            .filter(
                models.Schedule.organization_id
                == current_user.organization_id
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

    buses = (
        db.query(models.Bus)
        .filter(
            models.Bus.organization_id
            == current_user.organization_id,
            models.Bus.status == "AVAILABLE"
        )
        .all()
    )

    drivers = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == current_user.organization_id,
            models.Crew.role == "DRIVER",
            models.Crew.status == "AVAILABLE"
        )
        .all()
    )

    conductors = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == current_user.organization_id,
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

    existing_schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id
        )
        .all()
    )

    existing_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id,
            models.Duty.status != "CANCELLED"
        )
        .all()
    )

    result = generate_schedule(
        trips=unscheduled_trips,
        buses=buses,
        drivers=drivers,
        conductors=conductors,
        existing_schedules=existing_schedules,
        existing_duties=existing_duties
    )

    if not result["success"]:

        return result

    created_schedules = []

    for assignment in result["assignments"]:

        new_schedule = models.Schedule(
            organization_id=current_user.organization_id,
            trip_id=assignment["trip_id"],
            bus_id=assignment["bus_id"],
            driver_id=assignment["driver_id"],
            conductor_id=assignment["conductor_id"],
            scheduled_date=start_of_day,
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's conflicts"
        )

    schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id,
            models.Schedule.status != "CANCELLED"
        )
        .all()
    )

    duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id,
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
        "organization_id": current_user.organization_id,
        "total_conflicts": len(conflicts),
        "conflicts": conflicts
    }


# ==================================================
# ROUTE OVERLAP DETECTION
# ==================================================

@app.get("/routes/{route_id}/overlaps")
def get_route_overlaps(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    target_route = (
        db.query(models.Route)
        .filter(
            models.Route.id == route_id,
            models.Route.organization_id
            == current_user.organization_id
        )
        .first()
    )

    if not target_route:

        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    routes = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id
            == current_user.organization_id,
            models.Route.status == "ACTIVE"
        )
        .all()
    )

    stops = (
        db.query(models.Stop)
        .filter(
            models.Stop.organization_id
            == current_user.organization_id
        )
        .all()
    )

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


# ==================================================
# ROUTE MAP DATA
# ==================================================

@app.get("/routes/{route_id}/map-data")
def get_route_map_data(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    route = (
        db.query(models.Route)
        .filter(
            models.Route.id == route_id,
            models.Route.organization_id
            == current_user.organization_id
        )
        .first()
    )

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

        stop = (
            db.query(models.Stop)
            .filter(
                models.Stop.id == route_stop.stop_id,
                models.Stop.organization_id
                == current_user.organization_id
            )
            .first()
        )

        if stop:

            map_stops.append(
                {
                    "stop_id": stop.id,
                    "name": stop.name,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "sequence_number": route_stop.sequence_number
                }
            )

    coordinates = [
        [
            stop["latitude"],
            stop["longitude"]
        ]
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


# ==================================================
# DASHBOARD / ANALYTICS
# ==================================================

@app.get("/dashboard/{organization_id}")
def get_dashboard(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_authenticated_user)
):

    if organization_id != current_user.organization_id:

        raise HTTPException(
            status_code=403,
            detail="You cannot access another organization's dashboard"
        )

    total_buses = (
        db.query(models.Bus)
        .filter(
            models.Bus.organization_id
            == current_user.organization_id
        )
        .count()
    )

    available_buses = (
        db.query(models.Bus)
        .filter(
            models.Bus.organization_id
            == current_user.organization_id,
            models.Bus.status == "AVAILABLE"
        )
        .count()
    )

    total_crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == current_user.organization_id
        )
        .count()
    )

    available_crew = (
        db.query(models.Crew)
        .filter(
            models.Crew.organization_id
            == current_user.organization_id,
            models.Crew.status == "AVAILABLE"
        )
        .count()
    )

    total_routes = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id
            == current_user.organization_id
        )
        .count()
    )

    active_routes = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id
            == current_user.organization_id,
            models.Route.status == "ACTIVE"
        )
        .count()
    )

    total_trips = (
        db.query(models.Trip)
        .filter(
            models.Trip.organization_id
            == current_user.organization_id
        )
        .count()
    )

    scheduled_trips = (
        db.query(models.Trip)
        .filter(
            models.Trip.organization_id
            == current_user.organization_id,
            models.Trip.status == "SCHEDULED"
        )
        .count()
    )

    total_schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id
        )
        .count()
    )

    automatic_schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id,
            models.Schedule.duty_type == "AUTO"
        )
        .count()
    )

    manual_schedules = (
        total_schedules - automatic_schedules
    )

    total_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id
        )
        .count()
    )

    linked_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id,
            models.Duty.duty_type == "LINKED"
        )
        .count()
    )

    unlinked_duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id,
            models.Duty.duty_type == "UNLINKED"
        )
        .count()
    )

    schedules = (
        db.query(models.Schedule)
        .filter(
            models.Schedule.organization_id
            == current_user.organization_id
        )
        .all()
    )

    duties = (
        db.query(models.Duty)
        .filter(
            models.Duty.organization_id
            == current_user.organization_id
        )
        .all()
    )

    conflicts = detect_conflicts(
        schedules,
        duties
    )

    total_conflicts = len(conflicts)

    routes = (
        db.query(models.Route)
        .filter(
            models.Route.organization_id
            == current_user.organization_id
        )
        .all()
    )

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

            common_stops = (
                route1_stop_ids.intersection(
                    route2_stop_ids
                )
            )

            if len(common_stops) >= 2:

                route_overlap_pairs += 1

    return {
        "success": True,

        "organization_id":
            current_user.organization_id,

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


# ==================================================
# REGISTER USER
# ==================================================

@app.post("/register")
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(models.User)
        .filter(
            models.User.email == user.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    organization = (
        db.query(models.Organization)
        .filter(
            models.Organization.id
            == user.organization_id
        )
        .first()
    )

    if not organization:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    new_user = models.User(
        organization_id=user.organization_id,
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "message": "User registered successfully",
        "user_id": new_user.id
    }


# ==================================================
# LOGIN
# ==================================================

@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "user_id": user.id,
            "organization_id": user.organization_id,
            "role": user.role
        },
        expires_delta=timedelta(hours=24)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==================================================
# CURRENT USER / ME
# ==================================================

@app.get("/me")
def get_me(
    current_user: models.User = Depends(
        get_authenticated_user
    )
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "organization_id":
            current_user.organization_id,
        "role": current_user.role
    }