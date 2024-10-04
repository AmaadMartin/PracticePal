// src/Components/CreateExam.js
import React, { useState } from "react";
import "./CreateExam.css";

function CreateExam({ username, setExams, setSelectedExam, setExamQuestions }) {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    const uploadedFiles = Array.from(e.dataTransfer.files);
    setFiles(uploadedFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileUpload = async () => {
    setIsUploading(true);

    // Prepare form data
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("username", username); // Include username in the form data

    try {
      // Send files to the API
      const response = await fetch(`https://practicepal.onrender.com/create_exam/${username}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create exam');
      }

      const data = await response.json();

      // Assume the API returns the new exam with id, name, and questions
      const newExam = {
        id: data.id, // Ensure the API returns the exam's id
        name: data.name,
        questions: data.questions,
      };

      // Update examQuestions
      setExamQuestions((prev) => ({
        ...prev,
        [newExam.id]: newExam.questions,
      }));

      // Update exams list
      setExams((prev) => [...prev, { id: newExam.id, name: newExam.name }]);

      // Set the newly created exam as selected
      setSelectedExam(newExam.id);
    } catch (error) {
      console.error("Error uploading files:", error);
      alert("Failed to upload files. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="exam-content">
      <h1>Create New Exam</h1>
      <div className="dropzone" onDrop={handleDrop} onDragOver={handleDragOver}>
        {files.length === 0 ? (
          <p>Drag and drop files here, or click to select files</p>
        ) : (
          <ul>
            {files.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        )}
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
        />
      </div>
      <button
        onClick={handleFileUpload}
        disabled={files.length === 0 || isUploading}
        className="upload-button"
      >
        {isUploading ? "Uploading..." : "Create Exam"}
      </button>
    </div>
  );
}

export default CreateExam;
