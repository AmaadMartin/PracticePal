// src/Sidebar.js
import React from 'react';
import { Link } from 'react-router-dom';

function Sidebar({ exams, setSelectedExam }) {
  return (
    <div className="sidebar">
      <h2>Past Exams</h2>
      <ul>
        {exams.map((exam, index) => (
          <li key={index} onClick={() => setSelectedExam(exam)}>
            <Link to="/">{exam}</Link>
          </li>
        ))}
      </ul>
      <button className="create-button">
        <Link to="/create">+ Create New</Link>
      </button>
    </div>
  );
}

export default Sidebar;
