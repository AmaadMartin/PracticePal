// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './Components/Sidebar';
import Exam from './Components/Exam';
import CreateExam from './Components/CreateExam';
import Login from './Components/Login';
import ProtectedRoute from './Components/ProtectedRoute';
import Signup from './Components/Signup';
import PaymentSuccess from './Components/PaymentSuccess';
import './App.css';

function App() {
  const [selectedExam, setSelectedExam] = useState(null); // Store exam ID
  const [exams, setExams] = useState([]); // Array of { id, name }
  const [examQuestions, setExamQuestions] = useState({});
  const [username, setUsername] = useState('');

  // Fetch user exams when username is set
  useEffect(() => {
    if (username) {
      fetchUserExams(username);
    }
  }, [username]);

  const fetchUserExams = async (username) => {
    try {
      const response = await fetch(`https://practicepal.onrender.com/users/${username}`);
      if (!response.ok) {
        throw new Error('Failed to fetch user data');
      }
      const data = await response.json();

      // Assuming the API returns data in the new format
      const userExams = data.exams.map((exam) => ({
        id: exam.id, // Ensure each exam has a unique id
        name: exam.name,
        questions: exam.questions.map((q) => ({
          question: q.question,
          type: q.type,
          answer_choices: q.answer_choices?.map((choice) => choice) || [],
          correct_answer: q?.correct_answer || '',
          explanation: q?.explanation || '',
        })),
      }));

      setExams(userExams.map(({ id, name }) => ({ id, name })));
      const examQuestionsMap = {};
      userExams.forEach((exam) => {
        examQuestionsMap[exam.id] = exam.questions;
      });
      setExamQuestions(examQuestionsMap);
      if (userExams.length > 0) {
        setSelectedExam(userExams[0].id); // Set selectedExam to the first exam's id
      }
    } catch (error) {
      console.error('Error fetching user exams:', error);
      alert('Failed to fetch user data. Please check your username.');
    }
  };

  return (
    <Router>
      {username ? (
        <div className="app-container">
          <Sidebar
            exams={exams}
            setSelectedExam={setSelectedExam}
            selectedExam={selectedExam} // Pass the selectedExam ID
          />
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute isAuthenticated={!!username}>
                  <Exam
                    selectedExam={selectedExam}
                    examQuestions={examQuestions}
                    exams={exams} // Pass exams to display exam name
                    username={username} // Pass username
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/create"
              element={
                <ProtectedRoute isAuthenticated={!!username}>
                  <CreateExam
                    username={username}
                    setExams={setExams}
                    setSelectedExam={setSelectedExam}
                    setExamQuestions={setExamQuestions}
                  />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      ) : (
        <Routes>
          <Route path="/signup" element={<Signup />} />
          <Route path="/payment-success" element={<Navigate to="/login" />} />
          <Route path="/login" element={<Login setUsername={setUsername} />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      )}
    </Router>
  );
}

export default App;
