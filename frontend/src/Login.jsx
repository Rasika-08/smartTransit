import { useState } from "react";
import { API_URL } from "./api";

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded"
          },
          body: new URLSearchParams({
            username: email,
            password: password
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(
          data.detail ||
            "Invalid email or password"
        );
        return;
      }

      // Store JWT token
      localStorage.setItem(
        "access_token",
        data.access_token
      );

      // Store organization
      localStorage.setItem(
        "organization_id",
        "1"
      );

      console.log("Login successful");
      console.log(
        "Access token stored:",
        !!localStorage.getItem("access_token")
      );

      // Tell App.jsx that login was successful
      if (onLogin) {
        onLogin();
      }

    } catch (error) {
      console.error(
        "Login error:",
        error
      );

      setError(
        "Unable to connect to the backend."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#f4f6f8"
      }}
    >
      <div
        style={{
          width: "400px",
          background: "#ffffff",
          padding: "40px",
          borderRadius: "12px",
          boxShadow:
            "0 4px 20px rgba(0,0,0,0.1)"
        }}
      >
        <h1
          style={{
            textAlign: "center",
            marginBottom: "10px"
          }}
        >
          SmartTransit
        </h1>

        <p
          style={{
            textAlign: "center",
            color: "#666",
            marginBottom: "30px"
          }}
        >
          Bus Scheduling & Route Management
        </p>

        {error && (
          <div
            style={{
              background: "#fee2e2",
              color: "#b91c1c",
              padding: "12px",
              borderRadius: "6px",
              marginBottom: "20px"
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div
            style={{
              marginBottom: "20px"
            }}
          >
            <label
              style={{
                display: "block",
                marginBottom: "8px",
                fontWeight: "600"
              }}
            >
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="admin@smarttransit.com"
              required
              style={{
                width: "100%",
                padding: "12px",
                border: "1px solid #ccc",
                borderRadius: "6px",
                boxSizing: "border-box"
              }}
            />
          </div>

          <div
            style={{
              marginBottom: "25px"
            }}
          >
            <label
              style={{
                display: "block",
                marginBottom: "8px",
                fontWeight: "600"
              }}
            >
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              required
              style={{
                width: "100%",
                padding: "12px",
                border: "1px solid #ccc",
                borderRadius: "6px",
                boxSizing: "border-box"
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "13px",
              background: "#2563eb",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontSize: "16px",
              fontWeight: "600",
              cursor: loading
                ? "not-allowed"
                : "pointer"
            }}
          >
            {loading
              ? "Logging in..."
              : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;