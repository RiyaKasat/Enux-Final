import React, { useState, useRef } from 'react';
import { toast } from 'react-toastify';
import './FileUpload.css';

const FileUpload = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const allowedTypes = ['.pdf', '.txt', '.md', '.docx'];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const validateFile = (file) => {
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
      toast.error(`File type ${fileExt} not allowed. Supported: ${allowedTypes.join(', ')}`);
      return false;
    }
    
    if (file.size > maxFileSize) {
      toast.error('File size exceeds 10MB limit');
      return false;
    }
    
    return true;
  };

  const handleFileUpload = async (file) => {
    if (!validateFile(file)) return;

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          toast.success('File uploaded successfully!');
          onUploadComplete(response);
        } else {
          const error = JSON.parse(xhr.responseText);
          toast.error(error.error || 'Upload failed');
        }
        setUploading(false);
        setUploadProgress(0);
      });

      xhr.addEventListener('error', () => {
        toast.error('Upload failed');
        setUploading(false);
        setUploadProgress(0);
      });

      xhr.open('POST', `${process.env.REACT_APP_API_URL}/api/upload/file`);
      xhr.send(formData);

    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Upload failed');
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-dropzone ${isDragging ? 'dragging' : ''} ${uploading ? 'uploading' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={allowedTypes.join(',')}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          disabled={uploading}
        />
        
        {uploading ? (
          <div className="upload-progress">
            <div className="upload-spinner">
              <div className="spinner"></div>
            </div>
            <p>Uploading... {uploadProgress}%</p>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        ) : (
          <div className="upload-content">
            <div className="upload-icon">📄</div>
            <h3>Drop your file here or click to browse</h3>
            <p>Supported formats: PDF, TXT, MD, DOCX (max 10MB)</p>
            <button className="btn btn-primary btn-lg">
              Choose File
            </button>
          </div>
        )}
      </div>
      
      <div className="supported-formats">
        <h4>Supported Sources:</h4>
        <div className="format-grid">
          <div className="format-item">
            <span className="format-icon">📄</span>
            <span>PDF Documents</span>
          </div>
          <div className="format-item">
            <span className="format-icon">📝</span>
            <span>Text Files</span>
          </div>
          <div className="format-item">
            <span className="format-icon">📋</span>
            <span>Markdown</span>
          </div>
          <div className="format-item">
            <span className="format-icon">📄</span>
            <span>Word Docs</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
