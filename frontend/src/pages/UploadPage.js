import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import URLImport from '../components/URLImport';
import './UploadPage.css';

const UploadPage = () => {
  const [activeTab, setActiveTab] = useState('file');
  const navigate = useNavigate();

  const handleUploadComplete = (response) => {
    console.log('Upload completed:', response);
    if (response.upload_id) {
      navigate(`/playbook/${response.upload_id}`);
    }
  };

  const handleImportComplete = (response) => {
    console.log('Import completed:', response);
    if (response.upload_id) {
      navigate(`/playbook/${response.upload_id}`);
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-header">
        <h1>Import Your Playbook</h1>
        <p>Transform your existing knowledge into a version-controlled, collaborative playbook</p>
      </div>

      <div className="upload-tabs">
        <button
          className={`tab-button ${activeTab === 'file' ? 'active' : ''}`}
          onClick={() => setActiveTab('file')}
        >
          <span className="tab-icon">📁</span>
          Upload File
        </button>
        <button
          className={`tab-button ${activeTab === 'url' ? 'active' : ''}`}
          onClick={() => setActiveTab('url')}
        >
          <span className="tab-icon">🔗</span>
          Import from URL
        </button>
      </div>

      <div className="upload-content">
        {activeTab === 'file' && (
          <div className="tab-panel">
            <div className="tab-header">
              <h2>Upload Documents</h2>
              <p>Upload PDFs, Word docs, or text files to extract playbook content</p>
            </div>
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {activeTab === 'url' && (
          <div className="tab-panel">
            <div className="tab-header">
              <h2>Import from External Sources</h2>
              <p>Extract content from Notion, GitHub, Google Docs, or any website</p>
            </div>
            <URLImport onImportComplete={handleImportComplete} />
          </div>
        )}
      </div>

      <div className="upload-process">
        <h3>How it works:</h3>
        <div className="process-steps">
          <div className="process-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>Upload or Import</h4>
              <p>Choose your source - file upload or external URL</p>
            </div>
          </div>
          <div className="process-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>AI Extraction</h4>
              <p>Our AI extracts and categorizes content blocks</p>
            </div>
          </div>
          <div className="process-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Asset Mapping</h4>
              <p>Content is mapped to playbook assets (goals, strategies, tasks)</p>
            </div>
          </div>
          <div className="process-step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h4>Version Control</h4>
              <p>Your playbook is ready for collaboration and updates</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
