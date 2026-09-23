import { useEffect, useState } from "react";
import { apiFetch, API_URL } from "./api";

const ORGANIZATION_ID = 1;

function Reports() {
  const [trips, setTrips] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [buses, setBuses] = useState([]);
  const [crew, setCrew] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [conflicts, setConflicts] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        tripsResponse,
        schedulesResponse,
        busesResponse,
        crewResponse,
        routesResponse,
        conflictsResponse
      ] = await Promise.all([
        apiFetch(
          `${API_URL}/trips?organization_id=${ORGANIZATION_ID}`
        ),
        apiFetch(
          `${API_URL}/schedules?organization_id=${ORGANIZATION_ID}`
        ),
        apiFetch(
          `${API_URL}/buses?organization_id=${ORGANIZATION_ID}`
        ),
        apiFetch(
          `${API_URL}/crew?organization_id=${ORGANIZATION_ID}`
        ),
        apiFetch(
          `${API_URL}/routes?organization_id=${ORGANIZATION_ID}`
        ),
        apiFetch(
          `${API_URL}/conflicts/${ORGANIZATION_ID}`
        )
      ]);

      const responses = [
        tripsResponse,
        schedulesResponse,
        busesResponse,
        crewResponse,
        routesResponse,
        conflictsResponse
      ];

      const unauthorized = responses.some(
        (response) => response.status === 401
      );

      if (unauthorized) {
        throw new Error(
          "Authentication expired. Please login again."
        );
      }

      const failedResponse = responses.find(
        (response) => !response.ok
      );

      if (failedResponse) {
        throw new Error(
          `Backend request failed: ${failedResponse.status}`
        );
      }

      const tripsData =
        await tripsResponse.json();

      const schedulesData =
        await schedulesResponse.json();

      const busesData =
        await busesResponse.json();

      const crewData =
        await crewResponse.json();

      const routesData =
        await routesResponse.json();

      const conflictData =
        await conflictsResponse.json();

      setTrips(
        Array.isArray(tripsData)
          ? tripsData
          : []
      );

      setSchedules(
        Array.isArray(schedulesData)
          ? schedulesData
          : []
      );

      setBuses(
        Array.isArray(busesData)
          ? busesData
          : []
      );

      setCrew(
        Array.isArray(crewData)
          ? crewData
          : []
      );

      setRoutes(
        Array.isArray(routesData)
          ? routesData
          : []
      );

      setConflicts(
        Array.isArray(conflictData?.conflicts)
          ? conflictData.conflicts
          : []
      );

    } catch (error) {
      console.error(
        "Error loading reports:",
        error
      );

      setError(
        "Unable to load report data from the backend."
      );

    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = (filename, rows) => {
    if (!rows.length) {
      alert(
        "No data available for this report."
      );
      return;
    }

    const headers =
      Object.keys(rows[0]);

    const csv = [
      headers.join(","),
      ...rows.map((row) =>
        headers
          .map(
            (header) =>
              `"${String(
                row[header] ?? ""
              ).replace(/"/g, '""')}"`
          )
          .join(",")
      )
    ].join("\n");

    const blob = new Blob(
      [csv],
      {
        type: "text/csv;charset=utf-8;"
      }
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const scheduleReport = schedules.map(
    (schedule) => ({
      Schedule_ID: schedule.id,
      Trip_ID: schedule.trip_id,
      Bus_ID: schedule.bus_id,
      Driver_ID: schedule.driver_id,
      Conductor_ID:
        schedule.conductor_id,
      Start_Time:
        schedule.start_time,
      End_Time:
        schedule.end_time,
      Duty_Type:
        schedule.duty_type,
      Status:
        schedule.status
    })
  );

  const fleetReport = buses.map(
    (bus) => ({
      Bus_ID: bus.id,
      Bus_Number:
        bus.bus_number,
      Registration_Number:
        bus.registration_number,
      Capacity:
        bus.capacity,
      Bus_Type:
        bus.bus_type,
      Status:
        bus.status
    })
  );

  const crewReport = crew.map(
    (member) => ({
      Crew_ID: member.id,
      Name: member.name,
      Employee_ID:
        member.employee_id,
      Role: member.role,
      Phone: member.phone,
      Status: member.status
    })
  );

  const routeReport = routes.map(
    (route) => ({
      Route_ID: route.id,
      Route_Number:
        route.route_number,
      Route_Name:
        route.route_name,
      Start_Location:
        route.start_location,
      End_Location:
        route.end_location,
      Distance:
        route.distance,
      Estimated_Duration:
        route.estimated_duration,
      Status:
        route.status
    })
  );

  const conflictReport =
    conflicts.map(
      (conflict) => ({
        Type: conflict.type,
        Resource_ID:
          conflict.resource_id,
        Schedule_ID:
          conflict.schedule_id || "",
        Duty_ID:
          conflict.duty_id || "",
        Message:
          conflict.message
      })
    );

  const operationsReport = [
    {
      Metric: "Total Trips",
      Value: trips.length
    },
    {
      Metric: "Total Schedules",
      Value: schedules.length
    },
    {
      Metric: "Automatic Schedules",
      Value:
        schedules.filter(
          (s) =>
            s.duty_type === "AUTO"
        ).length
    },
    {
      Metric: "Manual Schedules",
      Value:
        schedules.filter(
          (s) =>
            s.duty_type !== "AUTO"
        ).length
    },
    {
      Metric: "Total Buses",
      Value: buses.length
    },
    {
      Metric: "Total Crew",
      Value: crew.length
    },
    {
      Metric: "Total Routes",
      Value: routes.length
    },
    {
      Metric: "Total Conflicts",
      Value: conflicts.length
    }
  ];

  if (loading) {
    return (
      <div className="dashboard-loading">
        Loading reports...
      </div>
    );
  }

  if (error) {
    return (
      <div className="management-page">

        <div className="management-card">

          <h3>Reports & Export</h3>

          <p>{error}</p>

          <button
            className="primary-button"
            onClick={loadReports}
          >
            Try Again
          </button>

        </div>

      </div>
    );
  }

  return (
    <div className="management-page">

      <div className="management-header">

        <div>
          <h2>Reports & Export</h2>

          <p>
            Generate operational reports and
            download them as CSV
          </p>
        </div>

        <button
          className="primary-button"
          onClick={loadReports}
        >
          Refresh Data
        </button>

      </div>

      <div className="reports-grid">

        <div className="report-card">
          <div className="report-icon">📅</div>

          <h3>Schedule Report</h3>

          <p>
            Export bus, driver, conductor and
            trip schedules.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              downloadCSV(
                "schedule_report.csv",
                scheduleReport
              )
            }
          >
            Download CSV
          </button>
        </div>

        <div className="report-card">
          <div className="report-icon">🚌</div>

          <h3>Fleet Report</h3>

          <p>
            Export all buses and their
            current status.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              downloadCSV(
                "fleet_report.csv",
                fleetReport
              )
            }
          >
            Download CSV
          </button>
        </div>

        <div className="report-card">
          <div className="report-icon">👥</div>

          <h3>Crew Report</h3>

          <p>
            Export driver and conductor
            information.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              downloadCSV(
                "crew_report.csv",
                crewReport
              )
            }
          >
            Download CSV
          </button>
        </div>

        <div className="report-card">
          <div className="report-icon">🛣️</div>

          <h3>Route Report</h3>

          <p>
            Export route details and
            operating status.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              downloadCSV(
                "route_report.csv",
                routeReport
              )
            }
          >
            Download CSV
          </button>
        </div>

        <div className="report-card">
          <div className="report-icon">⚠️</div>

          <h3>Conflict Report</h3>

          <p>
            Export detected scheduling
            conflicts.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              downloadCSV(
                "conflict_report.csv",
                conflictReport
              )
            }
          >
            Download CSV
          </button>
        </div>

        <div className="report-card">
          <div className="report-icon">📊</div>

          <h3>Operations Summary</h3>

          <p>
            Export a summary of transport
            operations.
          </p>

          <button
            className="primary-button"
            onClick={() =>
              downloadCSV(
                "operations_summary.csv",
                operationsReport
              )
            }
          >
            Download CSV
          </button>
        </div>

      </div>

    </div>
  );
}

export default Reports;