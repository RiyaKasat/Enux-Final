import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './PlaybookDetail.css';

const PlaybookDetail = () => {
  const { id } = useParams();
  const [playbook, setPlaybook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPlaybookDetails();
  }, [id]);

  const fetchPlaybookDetails = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/upload/${id}/status`);
      const data = await response.json();
      
      if (response.ok) {
        setPlaybook(data);
      } else {
        setError(data.error || 'Failed to load playbook');
      }
    } catch (error) {
      console.error('Error fetching playbook:', error);
      setError('Failed to load playbook');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="playbook-detail">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading playbook...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="playbook-detail">
        <div className="error-container">
          <div className="error-icon">❌</div>
          <h2>Error Loading Playbook</h2>
          <p>{error}</p>
          <button onClick={() => window.history.back()} className="btn btn-secondary">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'secondary';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'processing': return '⏳';
      case 'failed': return '❌';
      default: return '📄';
    }
  };

  return (
    <div className="playbook-detail">
      <div className="playbook-header">
        <div className="header-main">
          <h1>{playbook.original_name || 'Imported Playbook'}</h1>
          <div className="header-meta">
            <span className={`status-badge ${getStatusColor(playbook.status)}`}>
              <span className="status-icon">{getStatusIcon(playbook.status)}</span>
              {playbook.status}
            </span>
            <span className="upload-date">
              Uploaded {new Date(playbook.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        
        <div className="header-actions">
          <button className="btn btn-secondary">
            <span className="btn-icon">🔗</span>
            Fork
          </button>
          <button className="btn btn-primary">
            <span className="btn-icon">✏️</span>
            Edit
          </button>
        </div>
      </div>

      <div className="playbook-content">
        <div className="content-stats">
          <div className="stat-item">
            <div className="stat-label">File Size</div>
            <div className="stat-value">
              {playbook.file_size ? `${(playbook.file_size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}
            </div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Content Blocks</div>
            <div className="stat-value">{playbook.blocks_extracted || 0}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Source Type</div>
            <div className="stat-value">
              {playbook.source_url ? 'URL Import' : 'File Upload'}
            </div>
          </div>
          {playbook.processed_at && (
            <div className="stat-item">
              <div className="stat-label">Processed</div>
              <div className="stat-value">
                {new Date(playbook.processed_at).toLocaleString()}
              </div>
            </div>
          )}
        </div>

        {playbook.status === 'processing' && (
          <div className="processing-indicator">
            <div className="processing-animation">
              <div className="spinner"></div>
            </div>
            <h3>Processing Your Playbook</h3>
            <p>Our AI is extracting and categorizing content blocks. This usually takes 1-2 minutes.</p>
            <div className="processing-steps">
              <div className="step completed">
                <span className="step-icon">✅</span>
                File uploaded
              </div>
              <div className="step active">
                <span className="step-icon">⏳</span>
                Extracting content
              </div>
              <div className="step">
                <span className="step-icon">⭕</span>
                Mapping assets
              </div>
              <div className="step">
                <span className="step-icon">⭕</span>
                Generating embeddings
              </div>
            </div>
          </div>
        )}

        {playbook.status === 'completed' && playbook.blocks_extracted > 0 && (
          <div className="success-indicator">
            <div className="success-icon">🎉</div>
            <h3>Playbook Ready!</h3>
            <p>
              Successfully extracted <strong>{playbook.blocks_extracted} content blocks</strong> from your source.
              Your playbook is now ready for collaboration and version control.
            </p>
            
            <div className="next-steps">
              <h4>Next Steps:</h4>
              <div className="steps-grid">
                <div className="next-step">
                  <span className="step-icon">📝</span>
                  <div>
                    <strong>Review Content</strong>
                    <p>Check extracted blocks and asset mappings</p>
                  </div>
                </div>
                <div className="next-step">
                  <span className="step-icon">🏷️</span>
                  <div>
                    <strong>Add Metadata</strong>
                    <p>Tag your playbook and add descriptions</p>
                  </div>
                </div>
                <div className="next-step">
                  <span className="step-icon">🚀</span>
                  <div>
                    <strong>Publish</strong>
                    <p>Make your playbook available for collaboration</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {playbook.status === 'failed' && (
          <div className="error-indicator">
            <div className="error-icon">⚠️</div>
            <h3>Processing Failed</h3>
            <p>We encountered an error while processing your playbook:</p>
            <div className="error-message">
              {playbook.error_message || 'Unknown error occurred'}
            </div>
            <div className="error-actions">
              <button onClick={fetchPlaybookDetails} className="btn btn-primary">
                Retry
              </button>
              <button onClick={() => window.history.back()} className="btn btn-secondary">
                Go Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaybookDetail;
