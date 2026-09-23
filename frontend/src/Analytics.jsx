import { useEffect, useState } from "react";
import { apiFetch, API_URL } from "./api";

const ORGANIZATION_ID = 1;

function Analytics() {
  const [data, setData] = useState(null);
  const [crew, setCrew] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError("");

      const dashboardResponse = await apiFetch(
        `${API_URL}/dashboard/${ORGANIZATION_ID}`
      );

      const crewResponse = await apiFetch(
        `${API_URL}/crew?organization_id=${ORGANIZATION_ID}`
      );

      if (!dashboardResponse.ok) {
        throw new Error(
          `Dashboard request failed: ${dashboardResponse.status}`
        );
      }

      if (!crewResponse.ok) {
        throw new Error(
          `Crew request failed: ${crewResponse.status}`
        );
      }

      const dashboardData =
        await dashboardResponse.json();

      const crewData =
        await crewResponse.json();

      setData(dashboardData);

      setCrew(
        Array.isArray(crewData)
          ? crewData
          : []
      );

    } catch (error) {
      console.error(
        "Error loading analytics:",
        error
      );

      setError(
        "Unable to load analytics data."
      );

      setData(null);
      setCrew([]);

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        Loading analytics...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="management-page">

        <div className="management-card">
          <h3>Analytics</h3>

          <p>
            {error ||
              "Unable to load analytics data."}
          </p>

          <button
            className="primary-button"
            onClick={loadAnalytics}
          >
            Try Again
          </button>
        </div>

      </div>
    );
  }

  const drivers = crew.filter(
    (member) =>
      String(member.role || "").toUpperCase() ===
      "DRIVER"
  ).length;

  const conductors = crew.filter(
    (member) =>
      String(member.role || "").toUpperCase() ===
      "CONDUCTOR"
  ).length;

  const availabilityRate =
    data.buses.total > 0
      ? Math.round(
          (data.buses.available /
            data.buses.total) *
            100
        )
      : 0;

  const schedulingRate =
    data.trips.total > 0
      ? Math.round(
          (data.trips.scheduled /
            data.trips.total) *
            100
        )
      : 0;

  return (
    <div className="management-page">

      <div className="management-header">

        <div>
          <h2>Analytics & Reports</h2>

          <p>
            Overview of your transport operations
          </p>
        </div>

        <button
          className="primary-button"
          onClick={loadAnalytics}
        >
          Refresh
        </button>

      </div>

      <div className="analytics-grid">

        <div className="analytics-card">
          <div className="analytics-icon">🚌</div>

          <div>
            <h3>Total Buses</h3>

            <div className="analytics-number">
              {data.buses.total}
            </div>

            <p>
              {data.buses.available} available
            </p>
          </div>
        </div>

        <div className="analytics-card">
          <div className="analytics-icon">👥</div>

          <div>
            <h3>Total Crew</h3>

            <div className="analytics-number">
              {data.crew.total}
            </div>

            <p>
              {data.crew.available} available
            </p>
          </div>
        </div>

        <div className="analytics-card">
          <div className="analytics-icon">🛣️</div>

          <div>
            <h3>Active Routes</h3>

            <div className="analytics-number">
              {data.routes.active}
            </div>

            <p>
              of {data.routes.total} total routes
            </p>
          </div>
        </div>

        <div className="analytics-card">
          <div className="analytics-icon">📅</div>

          <div>
            <h3>Scheduled Trips</h3>

            <div className="analytics-number">
              {data.trips.scheduled}
            </div>

            <p>
              of {data.trips.total} total trips
            </p>
          </div>
        </div>

      </div>

      <div className="analytics-sections">

        <div className="management-card">
          <h3>Fleet Analytics</h3>

          <div className="analytics-row">
            <span>Total Buses</span>
            <strong>
              {data.buses.total}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Available Buses</span>
            <strong>
              {data.buses.available}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Unavailable Buses</span>
            <strong>
              {data.buses.total -
                data.buses.available}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Availability Rate</span>
            <strong>
              {availabilityRate}%
            </strong>
          </div>
        </div>

        <div className="management-card">
          <h3>Crew Analytics</h3>

          <div className="analytics-row">
            <span>Total Crew</span>
            <strong>
              {data.crew.total}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Available Crew</span>
            <strong>
              {data.crew.available}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Drivers</span>
            <strong>{drivers}</strong>
          </div>

          <div className="analytics-row">
            <span>Conductors</span>
            <strong>{conductors}</strong>
          </div>
        </div>

        <div className="management-card">
          <h3>Scheduling Analytics</h3>

          <div className="analytics-row">
            <span>Total Trips</span>
            <strong>
              {data.trips.total}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Scheduled Trips</span>
            <strong>
              {data.trips.scheduled}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Automatic Schedules</span>
            <strong>
              {data.schedules.automatic}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Manual Schedules</span>
            <strong>
              {data.schedules.manual}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Scheduling Rate</span>
            <strong>
              {schedulingRate}%
            </strong>
          </div>
        </div>

        <div className="management-card">
          <h3>Duty Analytics</h3>

          <div className="analytics-row">
            <span>Total Duties</span>
            <strong>
              {data.duties.total}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Linked Duties</span>
            <strong>
              {data.duties.linked}
            </strong>
          </div>

          <div className="analytics-row">
            <span>Unlinked Duties</span>
            <strong>
              {data.duties.unlinked}
            </strong>
          </div>
        </div>

      </div>

      <div className="management-card analytics-health">

        <h3>Operations Health</h3>

        <div className="health-grid">

          <div className="health-item">
            <span>Scheduling Conflicts</span>

            <strong
              className={
                data.conflicts.total === 0
                  ? "health-good"
                  : "health-warning"
              }
            >
              {data.conflicts.total}
            </strong>
          </div>

          <div className="health-item">
            <span>Route Overlaps</span>

            <strong>
              {data.route_overlaps.total}
            </strong>
          </div>

          <div className="health-item">
            <span>Automatic Schedules</span>

            <strong>
              {data.schedules.automatic}
            </strong>
          </div>

          <div className="health-item">
            <span>Manual Schedules</span>

            <strong>
              {data.schedules.manual}
            </strong>
          </div>

        </div>

      </div>

    </div>
  );
}

export default Analytics;