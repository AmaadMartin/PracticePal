// src/Components/Login.js

import React, { useState } from "react";
import { Link } from "react-router-dom";
import "./Login.css";

function Login({ setUsername }) {
  const [inputUsername, setInputUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!inputUsername.trim() || !password.trim()) {
      alert("Please enter both username and password.");
      return;
    }

    setIsLoggingIn(true);

    try {
      // Send username and password to login API
      console.log("here")
      console.log(process.env.REACT_APP_API_URL);
      const response = await fetch(`${process.env.REACT_APP_API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: inputUsername.trim(),
          password: password.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Login failed");
      }

      // If login is successful, set the username
      setUsername(inputUsername.trim());
    } catch (error) {
      console.error("Login error:", error);
      alert("Login failed. Please check your username and password.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="login-container">
      <img
        src="/PracticePalLogo.png"
        alt="Practice Pal Logo"
        className="logo"
      />
      <h1>Practice Pal</h1>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Enter your username"
          value={inputUsername}
          onChange={(e) => setInputUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" disabled={isLoggingIn}>
          {isLoggingIn ? "Logging in..." : "Login"}
        </button>
      </form>
      <p>
        Don't have an account? <Link to="/signup">Sign up here</Link>
      </p>
    </div>
  );
}

export default Login;
