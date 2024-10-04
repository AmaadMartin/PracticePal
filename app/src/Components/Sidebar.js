// src/Components/Sidebar.js

import React from 'react';
import { Link } from 'react-router-dom';
import './Sidebar.css'; // Import the corresponding CSS file
import { FaPlus } from 'react-icons/fa'; // Importing icons from react-icons

/**
 * Sidebar Component
 * 
 * Props:
 * - exams: Array of { id, name }
 * - setSelectedExam: Function to set the currently selected exam by ID
 * - selectedExam: The currently selected exam ID
 */
function Sidebar({ exams, setSelectedExam, selectedExam }) {

  /**
   * Handles the click event on an exam item.
   * Sets the selected exam by ID.
   * 
   * @param {string} examId - The ID of the exam clicked
   */
  const handleExamClick = (examId) => {
    setSelectedExam(examId);
  };

  return (
    <div className="sidebar">
      <h2>Exams</h2>
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
    </div>
  );
}

export default Sidebar;
