import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";
const ORGANIZATION_ID = 1;

function Conflict() {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadConflicts = async () => {
    try {
      setLoading(true);

      const response = await fetch(
        `${API_URL}/conflicts/${ORGANIZATION_ID}`
      );

      if (!response.ok) {
        throw new Error("Failed to load conflicts");
      }

      const data = await response.json();

      setConflicts(
        Array.isArray(data.conflicts)
          ? data.conflicts
          : []
      );

    } catch (error) {
      console.error("Error loading conflicts:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConflicts();
  }, []);

  const refreshConflicts = async () => {
    setRefreshing(true);

    await loadConflicts();

    setRefreshing(false);
  };

  const getConflictClass = (type) => {
    if (!type) {
      return "conflict-badge";
    }

    if (
      type.includes("OVERLAP")
    ) {
      return "conflict-badge overlap";
    }

    if (
      type.includes("REST")
    ) {
      return "conflict-badge rest";
    }

    return "conflict-badge";
  };

  return (
    <div className="management-page">

      <div className="management-header">

        <div>
          <h2>Conflict Management</h2>

          <p>
            Monitor scheduling conflicts and resource
            availability
          </p>
        </div>

        <button
          className="primary-button"
          onClick={refreshConflicts}
          disabled={refreshing}
        >
          {refreshing
            ? "Checking..."
            : "Refresh Conflicts"}
        </button>

      </div>

      {loading ? (

        <div className="management-card">
          <div className="empty-state">
            Checking scheduling conflicts...
          </div>
        </div>

      ) : conflicts.length === 0 ? (

        <div className="conflict-success">

          <div className="conflict-success-icon">
            ✓
          </div>

          <div>
            <h2>
              No Scheduling Conflicts
            </h2>

            <p>
              All current bus and crew assignments
              are conflict-free.
            </p>
          </div>

        </div>

      ) : (

        <>

          <div className="conflict-summary">

            <div className="conflict-count">
              <span>
                {conflicts.length}
              </span>

              <p>
                Active Conflict
                {conflicts.length !== 1
                  ? "s"
                  : ""}
              </p>
            </div>

          </div>

          <div className="management-card">

            <div className="table-header">

              <h3>
                Conflict Details
              </h3>

              <span>
                {conflicts.length} found
              </span>

            </div>

            <div className="table-container">

              <table>

                <thead>

                  <tr>
                    <th>Type</th>
                    <th>Resource</th>
                    <th>Schedule / Duty</th>
                    <th>Description</th>
                  </tr>

                </thead>

                <tbody>

                  {conflicts.map(
                    (conflict, index) => (

                      <tr key={index}>

                        <td>
                          <span
                            className={getConflictClass(
                              conflict.type
                            )}
                          >
                            {conflict.type}
                          </span>
                        </td>

                        <td>
                          {conflict.resource_id
                            ? `ID ${conflict.resource_id}`
                            : "-"}
                        </td>

                        <td>

                          {conflict.schedule_id && (
                            <div>
                              Schedule #
                              {conflict.schedule_id}
                            </div>
                          )}

                          {conflict.schedule_1 && (
                            <div>
                              Schedule #
                              {conflict.schedule_1}
                            </div>
                          )}

                          {conflict.schedule_2 && (
                            <div>
                              Schedule #
                              {conflict.schedule_2}
                            </div>
                          )}

                          {conflict.duty_id && (
                            <div>
                              Duty #
                              {conflict.duty_id}
                            </div>
                          )}

                        </td>

                        <td>
                          {conflict.message ||
                            "Scheduling conflict detected"}
                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          </div>

        </>

      )}

    </div>
  );
}

export default Conflict;