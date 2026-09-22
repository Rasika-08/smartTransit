import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";
import Fleet from "./Fleet";
import Crew from "./Crew";
import Scheduling from "./Scheduling";
import Conflict from "./Conflict";
import Duty from "./Duty";
import Analytics from "./Analytics";
import Reports from "./Reports";

const API_URL = "http://127.0.0.1:8000";

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png"
});

function App() {
  const [page, setPage] = useState("dashboard");

  const [routes, setRoutes] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [overlaps, setOverlaps] = useState([]);
  const [loading, setLoading] = useState(false);

  const [dashboard, setDashboard] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // -------------------------
  // LOAD DASHBOARD
  // -------------------------

  const loadDashboard = async () => {
    setDashboardLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/dashboard/1`
      );

      if (!response.ok) {
        throw new Error("Failed to load dashboard");
      }

      const data = await response.json();

      console.log("Dashboard Data:", data);

      setDashboard(data);

    } catch (error) {
      console.error(
        "Error loading dashboard:",
        error
      );
    } finally {
      setDashboardLoading(false);
    }
  };

  // -------------------------
  // LOAD ROUTES
  // -------------------------

  const loadRoutes = async () => {
    try {
      const response = await fetch(
        `${API_URL}/routes`
      );

      const data = await response.json();

      const routeList = Array.isArray(data)
        ? data
        : [data];

      setRoutes(routeList);

      if (routeList.length > 0) {
        loadRoute(routeList[0].id);
      }

    } catch (error) {
      console.error(
        "Error loading routes:",
        error
      );
    }
  };

  // -------------------------
  // LOAD SELECTED ROUTE
  // -------------------------

  const loadRoute = async (routeId) => {
    setLoading(true);

    try {
      const mapResponse = await fetch(
        `${API_URL}/routes/${routeId}/map-data`
      );

      if (!mapResponse.ok) {
        throw new Error(
          "Failed to load map data"
        );
      }

      const mapResult =
        await mapResponse.json();

      setMapData(mapResult);
      setSelectedRoute(routeId);

      const overlapResponse = await fetch(
        `${API_URL}/routes/${routeId}/overlaps`
      );

      if (!overlapResponse.ok) {
        throw new Error(
          "Failed to load overlap data"
        );
      }

      const overlapResult =
        await overlapResponse.json();

      setOverlaps(
        overlapResult.overlaps || []
      );

    } catch (error) {
      console.error(
        "Error loading route:",
        error
      );

      setOverlaps([]);

    } finally {
      setLoading(false);
    }
  };

  // -------------------------
  // INITIAL LOAD
  // -------------------------

  useEffect(() => {
    loadDashboard();
    loadRoutes();
  }, []);

  // -------------------------
  // MAP DATA
  // -------------------------

  const center =
    mapData?.coordinates?.length > 0
      ? mapData.coordinates[0]
      : [11.2215, 78.1765];

  const overlapStopIds =
    overlaps.flatMap(
      (overlap) =>
        overlap.common_stop_ids
    );

  const overlapCoordinates =
    mapData?.stops
      ?.filter((stop) =>
        overlapStopIds.includes(
          stop.stop_id
        )
      )
      .sort(
        (a, b) =>
          a.sequence_number -
          b.sequence_number
      )
      .map((stop) => [
        stop.latitude,
        stop.longitude
      ]) || [];

  // -------------------------
  // DASHBOARD PAGE
  // -------------------------

  const Dashboard = () => {

    if (dashboardLoading || !dashboard) {
      return (
        <div className="dashboard-loading">
          Loading dashboard...
        </div>
      );
    }

    return (
      <div className="dashboard">

        <div className="dashboard-title">
          <h2>Operations Dashboard</h2>

          <p>
            Real-time overview of your
            transport operations
          </p>
        </div>

        {/* TOP CARDS */}

        <div className="stats-grid">

          <div className="stat-card">
            <div className="stat-icon">
              🚌
            </div>

            <div>
              <h3>Buses</h3>

              <div className="stat-number">
                {dashboard.buses.total}
              </div>

              <p>
                {dashboard.buses.available}
                {" "}Available
              </p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              👥
            </div>

            <div>
              <h3>Crew</h3>

              <div className="stat-number">
                {dashboard.crew.total}
              </div>

              <p>
                {dashboard.crew.available}
                {" "}Available
              </p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              🛣️
            </div>

            <div>
              <h3>Routes</h3>

              <div className="stat-number">
                {dashboard.routes.total}
              </div>

              <p>
                {dashboard.routes.active}
                {" "}Active
              </p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              📅
            </div>

            <div>
              <h3>Trips</h3>

              <div className="stat-number">
                {dashboard.trips.total}
              </div>

              <p>
                {dashboard.trips.scheduled}
                {" "}Scheduled
              </p>
            </div>
          </div>

        </div>

        {/* SECOND ROW */}

        <div className="dashboard-grid">

          <div className="dashboard-card">

            <h3>
              Scheduling Overview
            </h3>

            <div className="dashboard-row">
              <span>
                Total Schedules
              </span>

              <strong>
                {dashboard.schedules.total}
              </strong>
            </div>

            <div className="dashboard-row">
              <span>
                Automatic
              </span>

              <strong>
                {dashboard.schedules.automatic}
              </strong>
            </div>

            <div className="dashboard-row">
              <span>
                Manual
              </span>

              <strong>
                {dashboard.schedules.manual}
              </strong>
            </div>

          </div>

          <div className="dashboard-card">

            <h3>
              Duty Management
            </h3>

            <div className="dashboard-row">
              <span>
                Total Duties
              </span>

              <strong>
                {dashboard.duties.total}
              </strong>
            </div>

            <div className="dashboard-row">
              <span>
                Linked Duties
              </span>

              <strong>
                {dashboard.duties.linked}
              </strong>
            </div>

            <div className="dashboard-row">
              <span>
                Unlinked Duties
              </span>

              <strong>
                {dashboard.duties.unlinked}
              </strong>
            </div>

          </div>

        </div>

        {/* STATUS CARDS */}

        <div className="status-grid">

          <div className="status-card success">

            <div>
              <h3>
                Schedule Conflicts
              </h3>

              <p>
                {dashboard.conflicts.total}
              </p>
            </div>

            <span>
              {dashboard.conflicts.total === 0
                ? "✓ No Conflicts"
                : "⚠ Conflicts Found"}
            </span>

          </div>

          <div className="status-card">

            <div>
              <h3>
                Route Overlaps
              </h3>

              <p>
                {dashboard.route_overlaps.total}
              </p>
            </div>

            <span>
              Routes with common stops
            </span>

          </div>

        </div>

      </div>
    );
  };

  // -------------------------
  // MAIN UI
  // -------------------------

  return (
    <div className="app">

      <header className="header">

        <div>
          <h1>SmartTransit</h1>

          <p>
            Bus Scheduling & Route Management System
          </p>
        </div>

        <div className="header-right">

          <button
            className={
              page === "dashboard"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => {
              setPage("dashboard");
              loadDashboard();
            }}
          >
            Dashboard
          </button>

          <button
            className={
              page === "routes"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => {
              setPage("routes");
              loadRoutes();
            }}
          >
            Routes & GIS
          </button>

          <button
            className={
              page === "fleet"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => setPage("fleet")}
          >
            Fleet
          </button>

          <button
            className={
              page === "crew"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => setPage("crew")}
          >
            Crew
          </button>

          <button
            className={
              page === "scheduling"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => setPage("scheduling")}
          >
            Scheduling
          </button>

          <button
            className={
              page === "conflict"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => setPage("conflict")}
          >
            Conflicts
          </button>

          <button
            className={
              page === "duty"
                ? "nav-button active"
                : "nav-button"
            }
            onClick={() => setPage("duty")}
          >
            Duties
          </button>
          <button
            className={`nav-button ${page === "analytics" ? "active" : ""}`}
            onClick={() => setPage("analytics")}
          >
            Analytics
          </button>
          <button
            className={`nav-button ${page === "reports" ? "active" : ""}`}
            onClick={() => setPage("reports")}
          >
            Reports
          </button>

          <div className="status">
            ● System Online
          </div>

        </div>

      </header>

      {page === "dashboard" && (
        <Dashboard />
      )}

      {page === "fleet" && (
        <Fleet />
      )}

      {page === "crew" && (
        <Crew />
      )}

      {page === "scheduling" && (
        <Scheduling />
      )}

      {page === "conflict" && (
        <Conflict />
      )}

      {page === "duty" && (
        <Duty />
      )}
      {page === "analytics" && <Analytics />}
      {page === "reports" && <Reports />}

      {page === "routes" && (

        <div className="content">

          <aside className="sidebar">

            <h2>Routes</h2>

            {routes.map((route) => (

              <button
                key={route.id}
                className={
                  selectedRoute === route.id
                    ? "route-button active"
                    : "route-button"
                }
                onClick={() =>
                  loadRoute(route.id)
                }
              >

                <strong>
                  Route {route.route_number}
                </strong>

                <span>
                  {route.route_name}
                </span>

              </button>

            ))}

            {mapData && (

              <div className="route-info">

                <h3>
                  Selected Route
                </h3>

                <p>
                  <strong>
                    {mapData.route_number}
                  </strong>
                </p>

                <p>
                  {mapData.route_name}
                </p>

                <hr />

                <p>
                  <strong>
                    Start:
                  </strong>
                  <br />
                  {mapData.start_location}
                </p>

                <p>
                  <strong>
                    End:
                  </strong>
                  <br />
                  {mapData.end_location}
                </p>

                <p>
                  <strong>
                    Stops:
                  </strong>{" "}
                  {mapData.stops.length}
                </p>

                {overlaps.length > 0 ? (

                  <div className="overlap-info">

                    <hr />

                    <h3>
                      Route Overlap Detected
                    </h3>

                    {overlaps.map(
                      (overlap) => (

                        <div
                          key={
                            overlap.route_id
                          }
                        >

                          <p>
                            <strong>
                              Overlaps with:
                            </strong>
                            <br />

                            Route{" "}
                            {overlap.route_number}
                            {" - "}
                            {overlap.route_name}
                          </p>

                          <p>
                            <strong>
                              Common Stops:
                            </strong>
                            <br />

                            {overlap.common_stops.join(
                              " → "
                            )}
                          </p>

                          <p>
                            <strong>
                              Overlap Count:
                            </strong>{" "}
                            {
                              overlap.overlap_count
                            }
                          </p>

                        </div>

                      )
                    )}

                  </div>

                ) : (

                  <div className="no-overlap">

                    <hr />

                    <p>
                      <strong>
                        Route Overlap:
                      </strong>
                      <br />

                      No overlapping routes
                      detected.
                    </p>

                  </div>

                )}

              </div>

            )}

          </aside>

          <main className="map-area">

            {loading ? (

              <div className="loading">
                Loading map...
              </div>

            ) : (

              <MapContainer
                center={center}
                zoom={14}
                className="map"
              >

                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {mapData?.stops?.map(
                  (stop) => (

                    <Marker
                      key={stop.stop_id}
                      position={[
                        stop.latitude,
                        stop.longitude
                      ]}
                    >

                      <Popup>

                        <strong>
                          {stop.name}
                        </strong>

                        <br />

                        Stop{" "}
                        {stop.sequence_number}

                      </Popup>

                    </Marker>

                  )
                )}

                {mapData?.coordinates?.length >
                  1 && (

                  <Polyline
                    positions={
                      mapData.coordinates
                    }
                    weight={6}
                  />

                )}

                {overlapCoordinates.length >
                  1 && (

                  <Polyline
                    positions={
                      overlapCoordinates
                    }
                    weight={10}
                  />

                )}

              </MapContainer>

            )}

          </main>

        </div>

      )}

    </div>
  );
}

export default App;