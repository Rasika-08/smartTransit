import { useEffect, useState } from "react";

import { apiFetch, API_URL } from "./api";

function Fleet() {
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    organization_id: 1,
    bus_number: "",
    registration_number: "",
    capacity: "",
    bus_type: "",
    status: "AVAILABLE"
  });

  const loadBuses = async () => {
    try {
      const response = await fetch(
        `${API_URL}/buses?organization_id=1`
      );

      const data = await response.json();

      const busList = Array.isArray(data)
        ? data
        : [data];

      setBuses(busList);
    } catch (error) {
      console.error("Error loading buses:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBuses();
  }, []);

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value
    });
  };

  const addBus = async (event) => {
    event.preventDefault();

    try {
      const response = await fetch(
        `${API_URL}/buses`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            organization_id: Number(form.organization_id),
            bus_number: form.bus_number,
            registration_number:
              form.registration_number,
            capacity: Number(form.capacity),
            bus_type: form.bus_type,
            status: form.status
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();

        alert(
          errorData.detail ||
          "Failed to add bus"
        );

        return;
      }

      alert("Bus added successfully");

      setForm({
        organization_id: 1,
        bus_number: "",
        registration_number: "",
        capacity: "",
        bus_type: "",
        status: "AVAILABLE"
      });

      setShowForm(false);

      loadBuses();

    } catch (error) {
      console.error("Error adding bus:", error);

      alert("Unable to connect to backend");
    }
  };

  return (
    <div className="management-page">

      <div className="management-header">

        <div>
          <h2>Fleet Management</h2>

          <p>
            Manage buses and fleet availability
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() =>
            setShowForm(!showForm)
          }
        >
          {showForm ? "Close" : "+ Add Bus"}
        </button>

      </div>

      {showForm && (

        <form
          className="bus-form"
          onSubmit={addBus}
        >

          <h3>Add New Bus</h3>

          <div className="form-grid">

            <div className="form-group">
              <label>Bus Number</label>

              <input
                name="bus_number"
                value={form.bus_number}
                onChange={handleChange}
                placeholder="BUS-102"
                required
              />
            </div>

            <div className="form-group">
              <label>Registration Number</label>

              <input
                name="registration_number"
                value={
                  form.registration_number
                }
                onChange={handleChange}
                placeholder="TN01AB1235"
                required
              />
            </div>

            <div className="form-group">
              <label>Capacity</label>

              <input
                name="capacity"
                type="number"
                value={form.capacity}
                onChange={handleChange}
                placeholder="50"
                required
              />
            </div>

            <div className="form-group">
              <label>Bus Type</label>

              <select
                name="bus_type"
                value={form.bus_type}
                onChange={handleChange}
                required
              >
                <option value="">
                  Select Type
                </option>

                <option value="ORDINARY">
                  Ordinary
                </option>

                <option value="AC">
                  AC
                </option>

                <option value="ELECTRIC">
                  Electric
                </option>

                <option value="CNG">
                  CNG
                </option>
              </select>
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

                <option value="MAINTENANCE">
                  Maintenance
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
            Save Bus
          </button>

        </form>

      )}

      <div className="management-card">

        <div className="table-header">

          <h3>
            Fleet Overview
          </h3>

          <span>
            {buses.length} Bus
            {buses.length !== 1 ? "es" : ""}
          </span>

        </div>

        {loading ? (

          <div className="empty-state">
            Loading fleet...
          </div>

        ) : buses.length === 0 ? (

          <div className="empty-state">
            No buses found.
          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>
                <tr>
                  <th>Bus Number</th>
                  <th>Registration</th>
                  <th>Capacity</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>

                {buses.map((bus) => (

                  <tr key={bus.id}>

                    <td>
                      <strong>
                        {bus.bus_number}
                      </strong>
                    </td>

                    <td>
                      {bus.registration_number}
                    </td>

                    <td>
                      {bus.capacity}
                    </td>

                    <td>
                      {bus.bus_type || "-"}
                    </td>

                    <td>

                      <span
                        className={
                          bus.status ===
                          "AVAILABLE"
                            ? "status-badge available"
                            : "status-badge"
                        }
                      >
                        {bus.status}
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

export default Fleet;