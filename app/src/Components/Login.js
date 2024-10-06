// src/Components/Login.js
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { GoogleLogin } from '@react-oauth/google';
import jwt_decode from 'jwt-decode';
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

  const handleGoogleLoginSuccess = async (credentialResponse) => {
    const { credential } = credentialResponse;

    // Send the credential (ID token) to your backend for verification
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/google-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credential }),
      });

      if (!response.ok) {
        throw new Error('Google login failed');
      }

      const data = await response.json();
      setUsername(data.username);
    } catch (error) {
      console.error('Google login error:', error);
      alert('Google login failed. Please try again.');
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

      {/* Google Sign-In Button */}
      <div className="google-login-container">
        <GoogleLogin
          onSuccess={handleGoogleLoginSuccess}
          onError={() => {
            console.log('Google Login Failed');
            alert('Google login failed. Please try again.');
          }}
          clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
        />
      </div>

      <p className="or-separator">OR</p>

      {/* Traditional Login Form */}
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
