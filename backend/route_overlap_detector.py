def detect_route_overlaps(target_route, other_routes, stop_names, min_common_stops=2):
    overlaps = []

    target_stops = sorted(
        target_route.route_stops,
        key=lambda x: x.sequence_number
    )

    target_stop_ids = [rs.stop_id for rs in target_stops]

    for route in other_routes:
        if route.id == target_route.id:
            continue

        other_stops = sorted(
            route.route_stops,
            key=lambda x: x.sequence_number
        )

        other_stop_ids = [rs.stop_id for rs in other_stops]

        best_overlap = []

        for i in range(len(target_stop_ids)):
            for j in range(len(other_stop_ids)):
                current_overlap = []

                x = i
                y = j

                while (
                    x < len(target_stop_ids)
                    and y < len(other_stop_ids)
                    and target_stop_ids[x] == other_stop_ids[y]
                ):
                    current_overlap.append(target_stop_ids[x])
                    x += 1
                    y += 1

                if len(current_overlap) > len(best_overlap):
                    best_overlap = current_overlap

        if len(best_overlap) >= min_common_stops:
            overlaps.append({
                "route_id": route.id,
                "route_number": route.route_number,
                "route_name": route.route_name,
                "common_stop_ids": best_overlap,
                "common_stops": [
                    stop_names.get(stop_id, f"Stop {stop_id}")
                    for stop_id in best_overlap
                ],
                "overlap_count": len(best_overlap)
            })

    return overlaps