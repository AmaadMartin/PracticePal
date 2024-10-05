// src/Components/Sidebar.js

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Sidebar.css';
import { FaPlus, FaBars } from 'react-icons/fa';

function Sidebar({ exams, setSelectedExam, selectedExam, credits }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleExamClick = (examId) => {
    setSelectedExam(examId);
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <button className="collapse-button" onClick={toggleSidebar}>
        <FaBars />
      </button>
      {!isCollapsed && (
        <>
          <h2>Exams</h2>
          <div className="credits-container">
            <div className="credits-box">
              <span>Exam Credits: {credits}</span>
            </div>
            <Link to="/purchase-credits" className="purchase-credits-button">
              <FaPlus />
            </Link>
          </div>
          <ul className="exam-list">
            {exams.map((exam) => (
              <li key={exam.id} onClick={() => handleExamClick(exam.id)}>
                <Link
                  to="/"
                  className={`exam-link ${selectedExam === exam.id ? 'active' : ''}`}
                >
                  <span className="exam-name">{exam.name}</span>
                </Link>
              </li>
            ))}
          </ul>
          <button className="create-button">
            <Link to="/create" className="create-link">
              <FaPlus className="plus-icon" /> Create New
            </Link>
          </button>
        </>
      )}
    </div>
  );
}

export default Sidebar;
