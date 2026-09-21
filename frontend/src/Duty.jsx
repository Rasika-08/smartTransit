import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";
const ORGANIZATION_ID = 1;

function Duty() {
  const [duties, setDuties] = useState([]);
  const [crew, setCrew] = useState([]);
  const [buses, setBuses] = useState([]);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");

  const [form, setForm] = useState({
    duty_name: "",
    duty_type: "LINKED",
    crew_id: "",
    bus_id: "",
    start_date: "2026-09-10",
    start_time: "07:30",
    end_date: "2026-09-10",
    end_time: "12:00",
    status: "PLANNED"
  });

  const loadData = async () => {
    try {
      setLoading(true);

      const [
        dutiesResponse,
        crewResponse,
        busesResponse
      ] = await Promise.all([
        fetch(
          `${API_URL}/duties?organization_id=${ORGANIZATION_ID}`
        ),
        fetch(
          `${API_URL}/crew?organization_id=${ORGANIZATION_ID}`
        ),
        fetch(
          `${API_URL}/buses?organization_id=${ORGANIZATION_ID}`
        )
      ]);

      if (!dutiesResponse.ok) {
        throw new Error("Failed to load duties");
      }

      if (!crewResponse.ok) {
        throw new Error("Failed to load crew");
      }

      if (!busesResponse.ok) {
        throw new Error("Failed to load buses");
      }

      const dutiesData = await dutiesResponse.json();
      const crewData = await crewResponse.json();
      const busesData = await busesResponse.json();

      setDuties(
        Array.isArray(dutiesData)
          ? dutiesData
          : dutiesData
            ? [dutiesData]
            : []
      );

      setCrew(
        Array.isArray(crewData)
          ? crewData
          : crewData
            ? [crewData]
            : []
      );

      setBuses(
        Array.isArray(busesData)
          ? busesData
          : busesData
            ? [busesData]
            : []
      );

    } catch (error) {
      console.error(
        "Error loading duty data:",
        error
      );

      showMessage(
        "Unable to load duty data from the backend.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showMessage = (text, type) => {
    setMessage(text);
    setMessageType(type);
  };

  const clearMessage = () => {
    setMessage("");
    setMessageType("");
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value
    }));

    clearMessage();
  };

  const getCrewName = (id) => {
    if (!id) {
      return "-";
    }

    const member = crew.find(
      (item) => item.id === Number(id)
    );

    return member
      ? `${member.name} (${member.role})`
      : `Crew ${id}`;
  };

  const getBusName = (id) => {
    if (!id) {
      return "Unassigned";
    }

    const bus = buses.find(
      (item) => item.id === Number(id)
    );

    return bus
      ? bus.bus_number
      : `Bus ${id}`;
  };

  const formatDateTime = (value) => {
    if (!value) {
      return "-";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString([], {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const createDuty = async (event) => {
    event.preventDefault();

    clearMessage();
    setCreating(true);

    try {
      if (!form.duty_name) {
        showMessage(
          "Please enter a duty name.",
          "error"
        );
        return;
      }

      if (!form.crew_id) {
        showMessage(
          "Please select a crew member.",
          "error"
        );
        return;
      }

      if (
        form.duty_type === "LINKED" &&
        !form.bus_id
      ) {
        showMessage(
          "A linked duty must have a bus assigned.",
          "error"
        );
        return;
      }

      const startDateTime =
        `${form.start_date}T${form.start_time}:00`;

      const endDateTime =
        `${form.end_date}T${form.end_time}:00`;

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

      const requestBody = {
        organization_id: ORGANIZATION_ID,
        duty_name: form.duty_name,
        duty_type: form.duty_type,
        crew_id: Number(form.crew_id),
        bus_id: form.bus_id
          ? Number(form.bus_id)
          : null,
        start_time: startDateTime,
        end_time: endDateTime,
        status: form.status
      };

      const response = await fetch(
        `${API_URL}/duties`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(requestBody)
        }
      );

      let data = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (response.status === 409) {
        showMessage(
          data?.detail ||
            "Duty conflict detected.",
          "error"
        );
        return;
      }

      if (!response.ok) {
        showMessage(
          data?.detail ||
            "Unable to create duty.",
          "error"
        );
        return;
      }

      showMessage(
        "Duty created successfully.",
        "success"
      );

      await loadData();

      setForm({
        duty_name: "",
        duty_type: "LINKED",
        crew_id: "",
        bus_id: "",
        start_date: "2026-09-10",
        start_time: "07:30",
        end_date: "2026-09-10",
        end_time: "12:00",
        status: "PLANNED"
      });

    } catch (error) {
      console.error(
        "Error creating duty:",
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

      <div className="management-header">

        <div>
          <h2>Duty Management</h2>

          <p>
            Manage linked and unlinked crew duties
          </p>
        </div>

      </div>

      {message && (
        <div
          className={`schedule-message ${messageType}`}
        >
          <strong>
            {messageType === "success"
              ? "Success"
              : "Attention"}
          </strong>

          <span>{message}</span>
        </div>
      )}

      <div className="management-card">

        <div className="table-header">

          <div>
            <h3>Create Duty</h3>

            <p>
              Assign crew and bus resources to a duty.
            </p>
          </div>

        </div>

        <form
          className="manual-schedule-form"
          onSubmit={createDuty}
        >

          <div className="form-grid">

            <div className="form-group">
              <label>Duty Name</label>

              <input
                name="duty_name"
                value={form.duty_name}
                onChange={handleChange}
                placeholder="Morning Linked Duty"
                required
              />
            </div>

            <div className="form-group">
              <label>Duty Type</label>

              <select
                name="duty_type"
                value={form.duty_type}
                onChange={handleChange}
              >
                <option value="LINKED">
                  LINKED
                </option>

                <option value="UNLINKED">
                  UNLINKED
                </option>
              </select>
            </div>

            <div className="form-group">
              <label>Crew Member</label>

              <select
                name="crew_id"
                value={form.crew_id}
                onChange={handleChange}
                required
              >
                <option value="">
                  Select Crew
                </option>

                {crew.map((member) => (
                  <option
                    key={member.id}
                    value={member.id}
                  >
                    {member.name} - {member.role}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>
                Bus
                {form.duty_type === "LINKED"
                  ? " *"
                  : ""}
              </label>

              <select
                name="bus_id"
                value={form.bus_id}
                onChange={handleChange}
              >
                <option value="">
                  {form.duty_type === "LINKED"
                    ? "Select Bus"
                    : "No Bus"}
                </option>

                {buses.map((bus) => (
                  <option
                    key={bus.id}
                    value={bus.id}
                  >
                    {bus.bus_number} -{" "}
                    {bus.registration_number}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Start Date</label>

              <input
                type="date"
                name="start_date"
                value={form.start_date}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Start Time</label>

              <input
                type="time"
                name="start_time"
                value={form.start_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>End Date</label>

              <input
                type="date"
                name="end_date"
                value={form.end_date}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>End Time</label>

              <input
                type="time"
                name="end_time"
                value={form.end_time}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Status</label>

              <select
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="PLANNED">
                  PLANNED
                </option>

                <option value="ACTIVE">
                  ACTIVE
                </option>

                <option value="COMPLETED">
                  COMPLETED
                </option>

                <option value="CANCELLED">
                  CANCELLED
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
                : "Create Duty"}
            </button>

          </div>

        </form>

      </div>

      <div className="management-card">

        <div className="table-header">

          <h3>Duty Overview</h3>

          <span>
            {duties.length} Duty
            {duties.length !== 1
              ? "ies"
              : ""}
          </span>

        </div>

        {loading ? (

          <div className="empty-state">
            Loading duties...
          </div>

        ) : duties.length === 0 ? (

          <div className="empty-state">
            No duties found.
          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>

                <tr>
                  <th>ID</th>
                  <th>Duty Name</th>
                  <th>Type</th>
                  <th>Crew</th>
                  <th>Bus</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Status</th>
                </tr>

              </thead>

              <tbody>

                {duties.map((duty) => (

                  <tr key={duty.id}>

                    <td>
                      #{duty.id}
                    </td>

                    <td>
                      <strong>
                        {duty.duty_name}
                      </strong>
                    </td>

                    <td>
                      <span className="status-badge">
                        {duty.duty_type}
                      </span>
                    </td>

                    <td>
                      {getCrewName(
                        duty.crew_id
                      )}
                    </td>

                    <td>
                      {getBusName(
                        duty.bus_id
                      )}
                    </td>

                    <td>
                      {formatDateTime(
                        duty.start_time
                      )}
                    </td>

                    <td>
                      {formatDateTime(
                        duty.end_time
                      )}
                    </td>

                    <td>

                      <span
                        className={
                          duty.status ===
                          "PLANNED"
                            ? "status-badge available"
                            : "status-badge"
                        }
                      >
                        {duty.status}
                      </span>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </div>

    </div>
  );
}

export default Duty;