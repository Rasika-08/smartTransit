import { useEffect, useState } from "react";
import { apiFetch, API_URL } from "./api";

const ORGANIZATION_ID = 1;

function Scheduling() {
  const [trips, setTrips] = useState([]);
  const [schedules, setSchedules] = useState([]);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [creating, setCreating] = useState(false);

  const [scheduleDate, setScheduleDate] =
    useState("2026-09-10");

  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");

  const [form, setForm] = useState({
    trip_id: "",
    bus_id: "",
    driver_id: "",
    conductor_id: "",
    scheduled_date: "2026-09-10",
    start_time: "13:30",
    end_time: "14:00",
    duty_type: "MANUAL",
    status: "SCHEDULED"
  });

  const showMessage = (text, type) => {
    setMessage(text);
    setMessageType(type);
  };

  const clearMessage = () => {
    setMessage("");
    setMessageType("");
  };

  const loadData = async () => {
    setLoading(true);

    try {
      const [
        tripsResponse,
        schedulesResponse
      ] = await Promise.all([
        apiFetch(
          `${API_URL}/trips?organization_id=${ORGANIZATION_ID}`
        ),
        apiFetch(
          `${API_URL}/schedules?organization_id=${ORGANIZATION_ID}`
        )
      ]);

      if (!tripsResponse.ok) {
        throw new Error(
          "Failed to load trips"
        );
      }

      if (!schedulesResponse.ok) {
        throw new Error(
          "Failed to load schedules"
        );
      }

      const tripsData =
        await tripsResponse.json();

      const schedulesData =
        await schedulesResponse.json();

      setTrips(
        Array.isArray(tripsData)
          ? tripsData
          : tripsData
            ? [tripsData]
            : []
      );

      setSchedules(
        Array.isArray(schedulesData)
          ? schedulesData
          : schedulesData
            ? [schedulesData]
            : []
      );
    } catch (error) {
      console.error(
        "Error loading scheduling data:",
        error
      );

      showMessage(
        "Unable to load scheduling data from the backend.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatTime = (value) => {
    if (!value) {
      return "-";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatDate = (value) => {
    if (!value) {
      return "-";
    }

    const date = new Date(
      `${value}T00:00:00`
    );

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleDateString([], {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  const getBusName = (busId) => {
    if (!busId) {
      return "Unassigned";
    }

    return `BUS-${busId}`;
  };

  const getCrewName = (crewId) => {
    if (!crewId) {
      return "Unassigned";
    }

    return `Crew ${crewId}`;
  };

  const getStatusClass = (status) => {
    if (status === "SCHEDULED") {
      return "status-badge available";
    }

    return "status-badge";
  };

  const handleFormChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value
    }));

    clearMessage();
  };

  // ==================================================
  // AUTOMATIC SCHEDULE GENERATION
  // ==================================================

  const generateSchedule = async () => {
    setGenerating(true);
    clearMessage();

    try {
      const response = await apiFetch(
        `${API_URL}/generate-schedule`,
        {
          method: "POST",
          body: JSON.stringify({
            organization_id: ORGANIZATION_ID,
            scheduled_date: form.scheduled_date
          })
        }
      );

      let data = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (
        data?.success === false &&
        data?.message ===
          "No unscheduled trips found for this date"
      ) {
        showMessage(
          `No unscheduled trips found for ${formatDate(
            form.scheduled_date
          )}. All trips for this date have already been scheduled.`,
          "info"
        );

        return;
      }

      if (!response.ok) {
        showMessage(
          data?.detail ||
            data?.message ||
            "Schedule generation failed.",
          "error"
        );

        return;
      }

      if (data?.success === true) {
        showMessage(
          data.message ||
            "Schedule generated successfully.",
          "success"
        );

        await loadData();

        return;
      }

      showMessage(
        data?.message ||
          "The scheduling operation could not be completed.",
        "error"
      );
    } catch (error) {
      console.error(
        "Error generating schedule:",
        error
      );

      showMessage(
        "Unable to connect to the backend.",
        "error"
      );
    } finally {
      setGenerating(false);
    }
  };

  // ==================================================
  // MANUAL SCHEDULE CREATION
  // ==================================================

  const createManualSchedule = async (event) => {
    event.preventDefault();

    clearMessage();
    setCreating(true);

    try {
      if (!form.trip_id) {
        showMessage(
          "Please enter a Trip ID.",
          "error"
        );
        return;
      }

      if (!form.bus_id) {
        showMessage(
          "Please enter a Bus ID.",
          "error"
        );
        return;
      }

      if (!form.driver_id) {
        showMessage(
          "Please enter a Driver ID.",
          "error"
        );
        return;
      }

      if (!form.conductor_id) {
        showMessage(
          "Please enter a Conductor ID.",
          "error"
        );
        return;
      }

      if (!form.scheduled_date) {
        showMessage(
          "Please select a scheduled date.",
          "error"
        );
        return;
      }

      if (!form.start_time) {
        showMessage(
          "Please select a start time.",
          "error"
        );
        return;
      }

      if (!form.end_time) {
        showMessage(
          "Please select an end time.",
          "error"
        );
        return;
      }

      const startDateTime =
        `${form.scheduled_date}T${form.start_time}:00`;

      const endDateTime =
        `${form.scheduled_date}T${form.end_time}:00`;

      if (
        new Date(endDateTime) <=
        new Date(startDateTime)
      ) {
        showMessage(
          "End time must be later than start time.",
          "error"
        );

        return;
      }

      // ==============================================
      // MANUAL SCHEDULE API REQUEST
      // ==============================================

      const response = await apiFetch(
        `${API_URL}/schedules`,
        {
          method: "POST",
          body: JSON.stringify({
            organization_id: ORGANIZATION_ID,
            trip_id: Number(form.trip_id),
            bus_id: Number(form.bus_id),
            driver_id: Number(form.driver_id),
            conductor_id: Number(form.conductor_id),
            scheduled_date:
              form.scheduled_date,
            start_time: startDateTime,
            end_time: endDateTime,
            duty_type: form.duty_type,
            status: form.status
          })
        }
      );

      let data = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      // ==============================================
      // CONFLICT DETECTED
      // ==============================================

      if (response.status === 409) {
        showMessage(
          data?.detail ||
            "Schedule conflict detected. The selected bus or crew is already assigned during this time.",
          "error"
        );

        return;
      }

      // ==============================================
      // OTHER BACKEND ERROR
      // ==============================================

      if (!response.ok) {
        showMessage(
          data?.detail ||
            data?.message ||
            "Unable to create the schedule.",
          "error"
        );

        return;
      }

      // ==============================================
      // SUCCESS
      // ==============================================

      showMessage(
        "Manual schedule created successfully.",
        "success"
      );

      await loadData();

      // Reset form
      setForm({
        trip_id: "",
        bus_id: "",
        driver_id: "",
        conductor_id: "",
        scheduled_date: scheduleDate,
        start_time: "13:30",
        end_time: "14:00",
        duty_type: "MANUAL",
        status: "SCHEDULED"
      });
    } catch (error) {
      console.error(
        "Error creating manual schedule:",
        error
      );

      showMessage(
        "Unable to connect to the backend.",
        "error"
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="management-page">

      {/* PAGE HEADER */}

      <div className="management-header">
        <div>
          <h2>Scheduling Management</h2>

          <p>
            Manage trips and generate optimized
            bus and crew schedules
          </p>
        </div>
      </div>

      {/* MESSAGE */}

      {message && (
        <div
          className={`schedule-message ${messageType}`}
        >
          <strong>
            {messageType === "success"
              ? "Success"
              : messageType === "info"
                ? "Information"
                : "Attention"}
          </strong>

          <span>
            {message}
          </span>
        </div>
      )}

      {/* AUTOMATIC SCHEDULING */}

      <div className="schedule-generator">

        <div>
          <h3>
            Automatic Schedule Generation
          </h3>

          <p>
            Generate bus and crew assignments
            using the scheduling engine.
          </p>
        </div>

        <div className="generator-controls">

          <div className="form-group">

            <label>
              Schedule Date
            </label>

            <input
              type="date"
              value={scheduleDate}
              onChange={(event) => {
                setScheduleDate(
                  event.target.value
                );

                setForm((previous) => ({
                  ...previous,
                  scheduled_date:
                    event.target.value
                }));

                clearMessage();
              }}
            />

          </div>

          <button
            className="primary-button"
            onClick={generateSchedule}
            disabled={
              generating ||
              !scheduleDate
            }
          >
            {generating
              ? "Generating..."
              : "Generate Schedule"}
          </button>

        </div>

      </div>

      {/* MANUAL SCHEDULE */}

      <div className="management-card">

        <div className="table-header">

          <div>
            <h3>
              Manual Schedule Creation
            </h3>

            <p>
              Assign a bus and crew to a trip
              manually.
            </p>
          </div>

        </div>

        <form
          className="manual-schedule-form"
          onSubmit={createManualSchedule}
        >

          <div className="form-grid">

            {/* TRIP */}

            <div className="form-group">

              <label>
                Trip ID
              </label>

              <input
                type="number"
                name="trip_id"
                min="1"
                placeholder="Example: 2"
                value={form.trip_id}
                onChange={handleFormChange}
              />

            </div>

            {/* BUS */}

            <div className="form-group">

              <label>
                Bus ID
              </label>

              <input
                type="number"
                name="bus_id"
                min="1"
                placeholder="Example: 2"
                value={form.bus_id}
                onChange={handleFormChange}
              />

            </div>

            {/* DRIVER */}

            <div className="form-group">

              <label>
                Driver ID
              </label>

              <input
                type="number"
                name="driver_id"
                min="1"
                placeholder="Example: 1"
                value={form.driver_id}
                onChange={handleFormChange}
              />

            </div>

            {/* CONDUCTOR */}

            <div className="form-group">

              <label>
                Conductor ID
              </label>

              <input
                type="number"
                name="conductor_id"
                min="1"
                placeholder="Example: 2"
                value={form.conductor_id}
                onChange={handleFormChange}
              />

            </div>

            {/* DATE */}

            <div className="form-group">

              <label>
                Scheduled Date
              </label>

              <input
                type="date"
                name="scheduled_date"
                value={form.scheduled_date}
                onChange={handleFormChange}
              />

            </div>

            {/* START TIME */}

            <div className="form-group">

              <label>
                Start Time
              </label>

              <input
                type="time"
                name="start_time"
                value={form.start_time}
                onChange={handleFormChange}
              />

            </div>

            {/* END TIME */}

            <div className="form-group">

              <label>
                End Time
              </label>

              <input
                type="time"
                name="end_time"
                value={form.end_time}
                onChange={handleFormChange}
              />

            </div>

            {/* DUTY TYPE */}

            <div className="form-group">

              <label>
                Duty Type
              </label>

              <select
                name="duty_type"
                value={form.duty_type}
                onChange={handleFormChange}
              >
                <option value="MANUAL">
                  MANUAL
                </option>

                <option value="LINKED">
                  LINKED
                </option>

                <option value="AUTO">
                  AUTO
                </option>
              </select>

            </div>

          </div>

          <div className="manual-form-actions">

            <button
              type="submit"
              className="primary-button"
              disabled={creating}
            >
              {creating
                ? "Creating..."
                : "Create Manual Schedule"}
            </button>

          </div>

        </form>

      </div>

      {/* TRIPS */}

      <div className="management-card">

        <div className="table-header">

          <h3>
            Trips
          </h3>

          <span>
            {trips.length} Trip
            {trips.length !== 1
              ? "s"
              : ""}
          </span>

        </div>

        {loading ? (

          <div className="empty-state">
            Loading trips...
          </div>

        ) : trips.length === 0 ? (

          <div className="empty-state">
            No trips found.
          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>

                <tr>
                  <th>ID</th>
                  <th>Route</th>
                  <th>Departure</th>
                  <th>Arrival</th>
                  <th>Bus</th>
                  <th>Driver</th>
                  <th>Conductor</th>
                  <th>Status</th>
                </tr>

              </thead>

              <tbody>

                {trips.map((trip) => (

                  <tr key={trip.id}>

                    <td>
                      #{trip.id}
                    </td>

                    <td>
                      Route {trip.route_id}
                    </td>

                    <td>
                      {formatTime(
                        trip.departure_time
                      )}
                    </td>

                    <td>
                      {formatTime(
                        trip.arrival_time
                      )}
                    </td>

                    <td>
                      {getBusName(
                        trip.bus_id
                      )}
                    </td>

                    <td>
                      {getCrewName(
                        trip.driver_id
                      )}
                    </td>

                    <td>
                      {getCrewName(
                        trip.conductor_id
                      )}
                    </td>

                    <td>

                      <span
                        className={getStatusClass(
                          trip.status
                        )}
                      >
                        {trip.status}
                      </span>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </div>

      {/* GENERATED SCHEDULES */}

      <div className="management-card schedule-list-card">

        <div className="table-header">

          <h3>
            Generated Schedules
          </h3>

          <span>
            {schedules.length} Schedule
            {schedules.length !== 1
              ? "s"
              : ""}
          </span>

        </div>

        {loading ? (

          <div className="empty-state">
            Loading schedules...
          </div>

        ) : schedules.length === 0 ? (

          <div className="empty-state">
            No schedules generated yet.
          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>

                <tr>
                  <th>ID</th>
                  <th>Trip</th>
                  <th>Bus</th>
                  <th>Driver</th>
                  <th>Conductor</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>

              </thead>

              <tbody>

                {schedules.map(
                  (schedule) => (

                    <tr
                      key={schedule.id}
                    >

                      <td>
                        #{schedule.id}
                      </td>

                      <td>
                        Trip{" "}
                        {schedule.trip_id}
                      </td>

                      <td>
                        {getBusName(
                          schedule.bus_id
                        )}
                      </td>

                      <td>
                        {getCrewName(
                          schedule.driver_id
                        )}
                      </td>

                      <td>
                        {getCrewName(
                          schedule.conductor_id
                        )}
                      </td>

                      <td>
                        {formatTime(
                          schedule.start_time
                        )}
                      </td>

                      <td>
                        {formatTime(
                          schedule.end_time
                        )}
                      </td>

                      <td>

                        <span className="status-badge">
                          {schedule.duty_type ||
                            "SCHEDULED"}
                        </span>

                      </td>

                      <td>

                        <span
                          className={getStatusClass(
                            schedule.status
                          )}
                        >
                          {schedule.status}
                        </span>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </div>

    </div>
  );
}

export default Scheduling;