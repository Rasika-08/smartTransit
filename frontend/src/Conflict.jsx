import { useEffect, useState } from "react";
import { apiFetch, API_URL } from "./api";

const ORGANIZATION_ID = 1;

function Conflict() {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadConflicts = async () => {
    setLoading(true);

    try {
      const response = await apiFetch(
        `${API_URL}/conflicts/${ORGANIZATION_ID}`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load conflicts"
        );
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setConflicts(data);
      } else {
        setConflicts(
          data.conflicts || []
        );
      }
    } catch (error) {
      console.error(
        "Error loading conflicts:",
        error
      );

      setConflicts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConflicts();
  }, []);

  return (
    <div className="management-page">
      <div className="management-header">
        <div>
          <h2>Schedule Conflicts</h2>

          <p>
            Detect bus and crew scheduling conflicts
          </p>
        </div>

        <button
          className="primary-button"
          onClick={loadConflicts}
        >
          Refresh
        </button>
      </div>

      <div className="management-card">
        <div className="table-header">
          <h3>Conflict Overview</h3>

          <span>
            {conflicts.length} Conflict
            {conflicts.length !== 1
              ? "s"
              : ""}
          </span>
        </div>

        {loading ? (
          <div className="empty-state">
            Checking conflicts...
          </div>
        ) : conflicts.length === 0 ? (
          <div className="empty-state">
            ✓ No scheduling conflicts detected.
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Resource</th>
                  <th>Schedule</th>
                  <th>Duty</th>
                  <th>Message</th>
                </tr>
              </thead>

              <tbody>
                {conflicts.map(
                  (conflict, index) => (
                    <tr
                      key={
                        conflict.id ||
                        index
                      }
                    >
                      <td>
                        <span className="status-badge">
                          {conflict.conflict_type ||
                            conflict.type ||
                            "-"}
                        </span>
                      </td>

                      <td>
                        {conflict.resource_id ||
                          "-"}
                      </td>

                      <td>
                        {conflict.schedule_id ||
                          "-"}
                      </td>

                      <td>
                        {conflict.duty_id ||
                          "-"}
                      </td>

                      <td>
                        {conflict.message ||
                          "Conflict detected"}
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

export default Conflict;