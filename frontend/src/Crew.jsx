import { useEffect, useState } from "react";
import { apiFetch, API_URL } from "./api";

const ORGANIZATION_ID = 1;

function Crew() {
  const [crew, setCrew] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    organization_id: ORGANIZATION_ID,
    name: "",
    employee_id: "",
    role: "DRIVER",
    phone: "",
    status: "AVAILABLE"
  });

  const loadCrew = async () => {
    setLoading(true);

    try {
      const response = await apiFetch(
        `${API_URL}/crew?organization_id=${ORGANIZATION_ID}`
      );

      if (!response.ok) {
        throw new Error("Failed to load crew");
      }

      const data = await response.json();

      const crewList = Array.isArray(data)
        ? data
        : [data];

      setCrew(crewList);
    } catch (error) {
      console.error("Error loading crew:", error);
      setCrew([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCrew();
  }, []);

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value
    });
  };

  const addCrew = async (event) => {
    event.preventDefault();

    try {
      const response = await apiFetch(
        `${API_URL}/crew`,
        {
          method: "POST",
          body: JSON.stringify({
            organization_id: Number(
              form.organization_id
            ),
            name: form.name,
            employee_id: form.employee_id,
            role: form.role,
            phone: form.phone,
            status: form.status
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();

        alert(
          errorData.detail ||
            "Failed to add crew member"
        );

        return;
      }

      alert("Crew member added successfully");

      setForm({
        organization_id: ORGANIZATION_ID,
        name: "",
        employee_id: "",
        role: "DRIVER",
        phone: "",
        status: "AVAILABLE"
      });

      setShowForm(false);

      await loadCrew();
    } catch (error) {
      console.error("Error adding crew:", error);
      alert("Unable to connect to backend");
    }
  };

  return (
    <div className="management-page">
      <div className="management-header">
        <div>
          <h2>Crew Management</h2>
          <p>
            Manage drivers, conductors and crew availability
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Close" : "+ Add Crew"}
        </button>
      </div>

      {showForm && (
        <form
          className="bus-form"
          onSubmit={addCrew}
        >
          <h3>Add Crew Member</h3>

          <div className="form-grid">
            <div className="form-group">
              <label>Name</label>

              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="Arun Kumar"
                required
              />
            </div>

            <div className="form-group">
              <label>Employee ID</label>

              <input
                name="employee_id"
                value={form.employee_id}
                onChange={handleChange}
                placeholder="DRV-002"
                required
              />
            </div>

            <div className="form-group">
              <label>Role</label>

              <select
                name="role"
                value={form.role}
                onChange={handleChange}
              >
                <option value="DRIVER">
                  Driver
                </option>

                <option value="CONDUCTOR">
                  Conductor
                </option>
              </select>
            </div>

            <div className="form-group">
              <label>Phone</label>

              <input
                name="phone"
                value={form.phone}
                onChange={handleChange}
                placeholder="9876543210"
              />
            </div>

            <div className="form-group">
              <label>Status</label>

              <select
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="AVAILABLE">
                  Available
                </option>

                <option value="ON_DUTY">
                  On Duty
                </option>

                <option value="LEAVE">
                  Leave
                </option>

                <option value="INACTIVE">
                  Inactive
                </option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            className="primary-button"
          >
            Save Crew
          </button>
        </form>
      )}

      <div className="management-card">
        <div className="table-header">
          <h3>Crew Overview</h3>

          <span>
            {crew.length} Crew Member
            {crew.length !== 1 ? "s" : ""}
          </span>
        </div>

        {loading ? (
          <div className="empty-state">
            Loading crew...
          </div>
        ) : crew.length === 0 ? (
          <div className="empty-state">
            No crew members found.
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Employee ID</th>
                  <th>Role</th>
                  <th>Phone</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {crew.map((member) => (
                  <tr key={member.id}>
                    <td>
                      <strong>
                        {member.name}
                      </strong>
                    </td>

                    <td>
                      {member.employee_id}
                    </td>

                    <td>{member.role}</td>

                    <td>
                      {member.phone || "-"}
                    </td>

                    <td>
                      <span
                        className={
                          member.status ===
                          "AVAILABLE"
                            ? "status-badge available"
                            : "status-badge"
                        }
                      >
                        {member.status}
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

export default Crew;