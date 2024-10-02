// src/App.js
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './Components/Sidebar';
import Exam from './Components/Exam';
import CreateExam from './Components/CreateExam';
import './App.css';

function App() {
  const [selectedExam, setSelectedExam] = useState('Practice Pal');
  const [exams, setExams] = useState([
  ]);

  const [examQuestions, setExamQuestions] = useState({});

  return (
    <Router>
      <div className="app-container">
        <Sidebar exams={exams} setSelectedExam={setSelectedExam} />
        <Routes>
          <Route
            path="/"
            element={
              <Exam
                selectedExam={selectedExam}
                examQuestions={examQuestions}
              />
            }
          />
          <Route
            path="/create"
            element={
              <CreateExam
                setExams={setExams}
                setSelectedExam={setSelectedExam}
                setExamQuestions={setExamQuestions}
              />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
