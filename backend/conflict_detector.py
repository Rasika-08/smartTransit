from datetime import timedelta


MIN_REST_MINUTES = 30


def trips_overlap(start1, end1, start2, end2):
    return start1 < end2 and end1 > start2


def has_sufficient_rest(end1, start2):
    if end1 > start2:
        return False

    return (start2 - end1) >= timedelta(minutes=MIN_REST_MINUTES)


def detect_conflicts(schedules, duties):

    conflicts = []

    # ==================================================
    # 1. SCHEDULE vs SCHEDULE
    # ==================================================

    for i in range(len(schedules)):
        for j in range(i + 1, len(schedules)):

            schedule1 = schedules[i]
            schedule2 = schedules[j]

            # ------------------------------
            # BUS CONFLICT
            # ------------------------------

            if schedule1.bus_id == schedule2.bus_id:

                if trips_overlap(
                    schedule1.start_time,
                    schedule1.end_time,
                    schedule2.start_time,
                    schedule2.end_time
                ):

                    conflicts.append({
                        "type": "BUS_OVERLAP",
                        "resource_id": schedule1.bus_id,
                        "schedule_1": schedule1.id,
                        "schedule_2": schedule2.id,
                        "message": "Same bus is assigned to overlapping schedules"
                    })

            # ------------------------------
            # DRIVER CONFLICT
            # ------------------------------

            if schedule1.driver_id == schedule2.driver_id:

                if trips_overlap(
                    schedule1.start_time,
                    schedule1.end_time,
                    schedule2.start_time,
                    schedule2.end_time
                ):

                    conflicts.append({
                        "type": "DRIVER_OVERLAP",
                        "resource_id": schedule1.driver_id,
                        "schedule_1": schedule1.id,
                        "schedule_2": schedule2.id,
                        "message": "Same driver is assigned to overlapping schedules"
                    })

                else:

                    if schedule1.end_time <= schedule2.start_time:

                        if not has_sufficient_rest(
                            schedule1.end_time,
                            schedule2.start_time
                        ):

                            conflicts.append({
                                "type": "DRIVER_REST",
                                "resource_id": schedule1.driver_id,
                                "schedule_1": schedule1.id,
                                "schedule_2": schedule2.id,
                                "message": "Driver does not have the required 30-minute rest period"
                            })

                    elif schedule2.end_time <= schedule1.start_time:

                        if not has_sufficient_rest(
                            schedule2.end_time,
                            schedule1.start_time
                        ):

                            conflicts.append({
                                "type": "DRIVER_REST",
                                "resource_id": schedule1.driver_id,
                                "schedule_1": schedule1.id,
                                "schedule_2": schedule2.id,
                                "message": "Driver does not have the required 30-minute rest period"
                            })

            # ------------------------------
            # CONDUCTOR CONFLICT
            # ------------------------------

            if schedule1.conductor_id == schedule2.conductor_id:

                if trips_overlap(
                    schedule1.start_time,
                    schedule1.end_time,
                    schedule2.start_time,
                    schedule2.end_time
                ):

                    conflicts.append({
                        "type": "CONDUCTOR_OVERLAP",
                        "resource_id": schedule1.conductor_id,
                        "schedule_1": schedule1.id,
                        "schedule_2": schedule2.id,
                        "message": "Same conductor is assigned to overlapping schedules"
                    })

                else:

                    if schedule1.end_time <= schedule2.start_time:

                        if not has_sufficient_rest(
                            schedule1.end_time,
                            schedule2.start_time
                        ):

                            conflicts.append({
                                "type": "CONDUCTOR_REST",
                                "resource_id": schedule1.conductor_id,
                                "schedule_1": schedule1.id,
                                "schedule_2": schedule2.id,
                                "message": "Conductor does not have the required 30-minute rest period"
                            })

                    elif schedule2.end_time <= schedule1.start_time:

                        if not has_sufficient_rest(
                            schedule2.end_time,
                            schedule1.start_time
                        ):

                            conflicts.append({
                                "type": "CONDUCTOR_REST",
                                "resource_id": schedule1.conductor_id,
                                "schedule_1": schedule1.id,
                                "schedule_2": schedule2.id,
                                "message": "Conductor does not have the required 30-minute rest period"
                            })

    # ==================================================
    # 2. SCHEDULE vs DUTY
    # ==================================================

    for schedule in schedules:

        for duty in duties:

            # ------------------------------------------
            # Ignore the duty if it represents the same
            # linked assignment as the schedule
            # ------------------------------------------

            same_linked_assignment = (
                duty.duty_type == "LINKED"
                and duty.bus_id == schedule.bus_id
                and duty.crew_id in [
                    schedule.driver_id,
                    schedule.conductor_id
                ]
            )

            if same_linked_assignment:
                continue

            # ------------------------------------------
            # BUS vs DUTY
            # ------------------------------------------

            if (
                duty.bus_id is not None
                and schedule.bus_id == duty.bus_id
            ):

                if trips_overlap(
                    schedule.start_time,
                    schedule.end_time,
                    duty.start_time,
                    duty.end_time
                ):

                    conflicts.append({
                        "type": "BUS_DUTY_OVERLAP",
                        "resource_id": schedule.bus_id,
                        "schedule_id": schedule.id,
                        "duty_id": duty.id,
                        "message": "Bus is assigned to a schedule and duty at the same time"
                    })

            # ------------------------------------------
            # CREW vs DUTY
            # ------------------------------------------

            if duty.crew_id in [
                schedule.driver_id,
                schedule.conductor_id
            ]:

                if trips_overlap(
                    schedule.start_time,
                    schedule.end_time,
                    duty.start_time,
                    duty.end_time
                ):

                    conflicts.append({
                        "type": "CREW_DUTY_OVERLAP",
                        "resource_id": duty.crew_id,
                        "schedule_id": schedule.id,
                        "duty_id": duty.id,
                        "message": "Crew member is assigned to a schedule and duty at the same time"
                    })

                else:

                    if schedule.end_time <= duty.start_time:

                        if not has_sufficient_rest(
                            schedule.end_time,
                            duty.start_time
                        ):

                            conflicts.append({
                                "type": "CREW_DUTY_REST",
                                "resource_id": duty.crew_id,
                                "schedule_id": schedule.id,
                                "duty_id": duty.id,
                                "message": "Crew member does not have the required 30-minute rest period"
                            })

                    elif duty.end_time <= schedule.start_time:

                        if not has_sufficient_rest(
                            duty.end_time,
                            schedule.start_time
                        ):

                            conflicts.append({
                                "type": "CREW_DUTY_REST",
                                "resource_id": duty.crew_id,
                                "schedule_id": schedule.id,
                                "duty_id": duty.id,
                                "message": "Crew member does not have the required 30-minute rest period"
                            })

    # ==================================================
    # RETURN RESULTS
    # ==================================================

    return conflicts