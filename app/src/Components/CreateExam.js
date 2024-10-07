// src/Components/CreateExam.js
import React, { useState } from "react";
import "./CreateExam.css";

function CreateExam({ username, setExams, setSelectedExam, setExamQuestions, setCredits }) {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const [className, setClassName] = useState("");
  const [school, setSchool] = useState("");
  const [topics, setTopics] = useState("");

  const MAX_FILES = 10;

  const handleDrop = (e) => {
    e.preventDefault();
    const uploadedFiles = Array.from(e.dataTransfer.files);
    
    if (uploadedFiles.length > MAX_FILES) {
      alert(`You can only upload a maximum of ${MAX_FILES} files.`);
      setFiles(uploadedFiles.slice(0, MAX_FILES));
    } else {
      setFiles(uploadedFiles);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    if (selectedFiles.length > MAX_FILES) {
      alert(`You can only upload a maximum of ${MAX_FILES} files.`);
      setFiles(selectedFiles.slice(0, MAX_FILES));
    } else {
      setFiles(selectedFiles);
    }
  };

  const handleFileUpload = async () => {
    if (!className || !school || !topics) {
      alert("Please fill in the class name, school, and topics.");
      return;
    }

    setIsUploading(true);

    // Prepare form data
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("user_id", username);
    formData.append("class_name", className);
    formData.append("school", school);
    formData.append("topics", topics);

    try {
      // Send data to the API
      const response = await fetch(`${process.env.REACT_APP_API_URL}/create_exam/${username}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create exam');
      }

      const data = await response.json();

      if (data.message !== 'success') {
        alert(data.message);
        return;
      }
      setCredits((prev) => prev - 1);

      // Assume the API returns the new exam with id, name, and questions
      const newExam = {
        id: data.id,
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
      
      // Clear the selected files and inputs after successful upload
      setFiles([]);
      setClassName("");
      setSchool("");
      setTopics("");
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

      <div className="input-group">
        <label htmlFor="className">Class Name:</label>
        <input
          type="text"
          id="className"
          value={className}
          onChange={(e) => setClassName(e.target.value)}
          placeholder="e.g., Calculus I"
        />
      </div>

      <div className="input-group">
        <label htmlFor="school">School:</label>
        <input
          type="text"
          id="school"
          value={school}
          onChange={(e) => setSchool(e.target.value)}
          placeholder="e.g., University of XYZ"
        />
      </div>

      <div className="input-group">
        <label htmlFor="topics">Topics (comma-separated):</label>
        <input
          type="text"
          id="topics"
          value={topics}
          onChange={(e) => setTopics(e.target.value)}
          placeholder="e.g., Limits, Derivatives, Integrals"
        />
      </div>

      <div
        className="dropzone"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        {files.length === 0 ? (
          <p>Drag and drop files here, or click to select files</p>
        ) : (
          <ul className="file-list">
            {files.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        )}
        <input
          type="file"
          multiple
          onChange={handleFileChange}
        />
        <p className="file-count">{files.length} / {MAX_FILES} files selected</p>
      </div>

      <button
        onClick={handleFileUpload}
        disabled={isUploading}
        className="upload-button"
      >
        {isUploading ? "Creating Exam..." : "Create Exam"}
      </button>
    </div>
  );
}

export default CreateExam;
