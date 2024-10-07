// src/Components/Signup.js

import React, { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import jwt_decode from 'jwt-decode';
import "./Signup.css";

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function Signup() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    tier: "free",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [isGoogleProcessing, setIsGoogleProcessing] = useState(false);

  const tiers = [
    {
      value: "free",
      label: "Free",
      price: "Free",
      features: ["4 exams a week"],
    },
    {
      value: "gold",
      label: "Gold Supporter",
      price: "$4.99/month",
      features: [
        "15 exams per week",
        "Automated Grading",
      ],
    },
    {
      value: "diamond",
      label: "Diamond Supporter",
      price: "$9.99/month",
      features: [
        "50 exams per week",
        "Automated Grading",
        "Detailed Answer Analysis and Explanations",
      ],
    },
  ];

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleTierSelect = (tierValue) => {
    setFormData({
      ...formData,
      tier: tierValue,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.sessionId) {
        const stripe = await stripePromise;
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
      } else if (data.free) {
        window.location.href = "/login";
      } else {
        alert("Failed to create Stripe session.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGoogleSignupSuccess = async (credentialResponse) => {
    const { credential } = credentialResponse;
    setIsGoogleProcessing(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/google-signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: credential,
          tier: formData.tier,
        }),
      });

      const data = await response.json();

      if (data.sessionId) {
        const stripe = await stripePromise;
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
      } else if (data.free) {
        window.location.href = "/login";
      } else {
        alert("Failed to process Google signup.");
      }
    } catch (error) {
      console.error("Google Signup Error:", error);
      alert("An error occurred during Google signup. Please try again.");
    } finally {
      setIsGoogleProcessing(false);
    }
  };

  return (
    <div className="signup-container">
      <h1>Sign Up</h1>
      <form onSubmit={handleSubmit}>
        {/* Email and Password Fields */}
        <input
          type="email"
          name="email"
          placeholder="Enter your email"
          value={formData.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Create a password"
          value={formData.password}
          onChange={handleChange}
          required
        />

        {/* Tier Selection */}
        <div className="tier-options">
          {tiers.map((tier) => (
            <div
              key={tier.value}
              className={`tier-card ${
                formData.tier === tier.value ? "selected" : ""
              }`}
              onClick={() => handleTierSelect(tier.value)}
            >
              <h2>{tier.label}</h2>
              <p className="price">{tier.price}</p>
              <ul>
                {tier.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Submit Button */}
        <button type="submit" disabled={isProcessing}>
          {isProcessing ? "Processing..." : "Sign Up"}
        </button>
      </form>

      <p>Or sign up with:</p>

      {/* Google Sign Up Button */}
      <GoogleLogin
        onSuccess={handleGoogleSignupSuccess}
        onError={() => {
          console.log('Google Signup Failed');
          alert('Google signup failed. Please try again.');
        }}
        disabled={isGoogleProcessing}
        clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}
      />


      {isGoogleProcessing && <p>Processing Google signup...</p>}

      <p>
        Already have an account? <a href="/login">Log in here</a>
      </p>
    </div>
  );
}

export default Signup;
