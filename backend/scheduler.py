from datetime import timedelta

from ortools.sat.python import cp_model


MIN_REST_MINUTES = 30


def trips_overlap(start1, end1, start2, end2):
    """
    Check whether two time periods overlap.
    """
    return start1 < end2 and end1 > start2


def crew_conflict(start1, end1, start2, end2):
    """
    Crew members need at least 30 minutes rest
    between two assignments.
    """

    if trips_overlap(start1, end1, start2, end2):
        return True

    if end1 <= start2:
        return (start2 - end1) < timedelta(minutes=MIN_REST_MINUTES)

    if end2 <= start1:
        return (start1 - end2) < timedelta(minutes=MIN_REST_MINUTES)

    return True


def generate_schedule(
    trips,
    buses,
    drivers,
    conductors,
    existing_schedules,
    existing_duties
):
    """
    Automatically assign buses, drivers and conductors
    to trips using OR-Tools CP-SAT.
    """

    model = cp_model.CpModel()

    # --------------------------------------------------
    # No trips
    # --------------------------------------------------

    if not trips:
        return {
            "success": False,
            "message": "No unscheduled trips found",
            "assignments": []
        }

    # --------------------------------------------------
    # Variables
    # --------------------------------------------------

    bus_vars = {}
    driver_vars = {}
    conductor_vars = {}

    # --------------------------------------------------
    # Create assignment variables
    # --------------------------------------------------

    for trip in trips:

        # Bus variables
        for bus in buses:
            bus_vars[(trip.id, bus.id)] = model.NewBoolVar(
                f"trip_{trip.id}_bus_{bus.id}"
            )

        # Driver variables
        for driver in drivers:
            driver_vars[(trip.id, driver.id)] = model.NewBoolVar(
                f"trip_{trip.id}_driver_{driver.id}"
            )

        # Conductor variables
        for conductor in conductors:
            conductor_vars[(trip.id, conductor.id)] = model.NewBoolVar(
                f"trip_{trip.id}_conductor_{conductor.id}"
            )

    # --------------------------------------------------
    # Every trip must get exactly one bus,
    # one driver and one conductor
    # --------------------------------------------------

    for trip in trips:

        model.Add(
            sum(
                bus_vars[(trip.id, bus.id)]
                for bus in buses
            ) == 1
        )

        model.Add(
            sum(
                driver_vars[(trip.id, driver.id)]
                for driver in drivers
            ) == 1
        )

        model.Add(
            sum(
                conductor_vars[(trip.id, conductor.id)]
                for conductor in conductors
            ) == 1
        )

    # --------------------------------------------------
    # Check existing schedules and duties
    # --------------------------------------------------

    for trip in trips:

        # ==============================================
        # BUS AVAILABILITY
        # ==============================================

        for bus in buses:

            blocked = False

            # Existing schedules
            for schedule in existing_schedules:

                if schedule.bus_id != bus.id:
                    continue

                if trips_overlap(
                    trip.departure_time,
                    trip.arrival_time,
                    schedule.start_time,
                    schedule.end_time
                ):
                    blocked = True
                    break

            # Existing duties
            if not blocked:

                for duty in existing_duties:

                    if duty.bus_id != bus.id:
                        continue

                    if trips_overlap(
                        trip.departure_time,
                        trip.arrival_time,
                        duty.start_time,
                        duty.end_time
                    ):
                        blocked = True
                        break

            if blocked:
                model.Add(
                    bus_vars[(trip.id, bus.id)] == 0
                )

        # ==============================================
        # DRIVER AVAILABILITY
        # ==============================================

        for driver in drivers:

            blocked = False

            # Existing schedules
            for schedule in existing_schedules:

                if schedule.driver_id != driver.id:
                    continue

                if crew_conflict(
                    trip.departure_time,
                    trip.arrival_time,
                    schedule.start_time,
                    schedule.end_time
                ):
                    blocked = True
                    break

            # Existing duties
            if not blocked:

                for duty in existing_duties:

                    if duty.crew_id != driver.id:
                        continue

                    if crew_conflict(
                        trip.departure_time,
                        trip.arrival_time,
                        duty.start_time,
                        duty.end_time
                    ):
                        blocked = True
                        break

            if blocked:
                model.Add(
                    driver_vars[(trip.id, driver.id)] == 0
                )

        # ==============================================
        # CONDUCTOR AVAILABILITY
        # ==============================================

        for conductor in conductors:

            blocked = False

            # Existing schedules
            for schedule in existing_schedules:

                if schedule.conductor_id != conductor.id:
                    continue

                if crew_conflict(
                    trip.departure_time,
                    trip.arrival_time,
                    schedule.start_time,
                    schedule.end_time
                ):
                    blocked = True
                    break

            # Existing duties
            if not blocked:

                for duty in existing_duties:

                    if duty.crew_id != conductor.id:
                        continue

                    if crew_conflict(
                        trip.departure_time,
                        trip.arrival_time,
                        duty.start_time,
                        duty.end_time
                    ):
                        blocked = True
                        break

            if blocked:
                model.Add(
                    conductor_vars[(trip.id, conductor.id)] == 0
                )

    # --------------------------------------------------
    # Prevent bus conflicts between generated trips
    # --------------------------------------------------

    for i in range(len(trips)):

        for j in range(i + 1, len(trips)):

            trip1 = trips[i]
            trip2 = trips[j]

            if trips_overlap(
                trip1.departure_time,
                trip1.arrival_time,
                trip2.departure_time,
                trip2.arrival_time
            ):

                for bus in buses:

                    model.Add(
                        bus_vars[(trip1.id, bus.id)]
                        +
                        bus_vars[(trip2.id, bus.id)]
                        <= 1
                    )

    # --------------------------------------------------
    # Prevent driver conflicts + enforce rest period
    # --------------------------------------------------

    for i in range(len(trips)):

        for j in range(i + 1, len(trips)):

            trip1 = trips[i]
            trip2 = trips[j]

            if crew_conflict(
                trip1.departure_time,
                trip1.arrival_time,
                trip2.departure_time,
                trip2.arrival_time
            ):

                for driver in drivers:

                    model.Add(
                        driver_vars[(trip1.id, driver.id)]
                        +
                        driver_vars[(trip2.id, driver.id)]
                        <= 1
                    )

    # --------------------------------------------------
    # Prevent conductor conflicts + enforce rest period
    # --------------------------------------------------

    for i in range(len(trips)):

        for j in range(i + 1, len(trips)):

            trip1 = trips[i]
            trip2 = trips[j]

            if crew_conflict(
                trip1.departure_time,
                trip1.arrival_time,
                trip2.departure_time,
                trip2.arrival_time
            ):

                for conductor in conductors:

                    model.Add(
                        conductor_vars[(trip1.id, conductor.id)]
                        +
                        conductor_vars[(trip2.id, conductor.id)]
                        <= 1
                    )

    # --------------------------------------------------
    # Prefer using fewer buses
    # --------------------------------------------------

    bus_used = {}

    for bus in buses:

        bus_used[bus.id] = model.NewBoolVar(
            f"bus_used_{bus.id}"
        )

        for trip in trips:

            model.Add(
                bus_vars[(trip.id, bus.id)]
                <= bus_used[bus.id]
            )

    model.Minimize(
        sum(bus_used.values())
    )

    # --------------------------------------------------
    # Solve
    # --------------------------------------------------

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    # --------------------------------------------------
    # Check result
    # --------------------------------------------------

    if status not in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ]:

        return {
            "success": False,
            "message": (
                "No feasible schedule could be generated. "
                "There may not be enough buses or crew "
                "to satisfy the constraints."
            ),
            "assignments": []
        }

    # --------------------------------------------------
    # Extract assignments
    # --------------------------------------------------

    assignments = []

    for trip in trips:

        selected_bus = None
        selected_driver = None
        selected_conductor = None

        for bus in buses:

            if solver.Value(
                bus_vars[(trip.id, bus.id)]
            ):
                selected_bus = bus.id
                break

        for driver in drivers:

            if solver.Value(
                driver_vars[(trip.id, driver.id)]
            ):
                selected_driver = driver.id
                break

        for conductor in conductors:

            if solver.Value(
                conductor_vars[(trip.id, conductor.id)]
            ):
                selected_conductor = conductor.id
                break

        assignments.append(
            {
                "trip_id": trip.id,
                "bus_id": selected_bus,
                "driver_id": selected_driver,
                "conductor_id": selected_conductor,
                "start_time": trip.departure_time,
                "end_time": trip.arrival_time
            }
        )

    return {
        "success": True,
        "message": "Schedule generated successfully",
        "assignments": assignments
    }