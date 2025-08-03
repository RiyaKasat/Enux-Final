import React, { useState } from 'react';
import { toast } from 'react-toastify';
import './URLImport.css';

const URLImport = ({ onImportComplete }) => {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [importing, setImporting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url.trim()) {
      toast.error('Please enter a URL');
      return;
    }

    // Basic URL validation
    try {
      new URL(url);
    } catch {
      toast.error('Please enter a valid URL');
      return;
    }

    setImporting(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/upload/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          title: title.trim() || undefined,
          description: description.trim() || undefined,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('URL imported successfully!');
        onImportComplete(data);
        // Reset form
        setUrl('');
        setTitle('');
        setDescription('');
      } else {
        toast.error(data.error || 'Import failed');
      }
    } catch (error) {
      console.error('Import error:', error);
      toast.error('Failed to import URL');
    } finally {
      setImporting(false);
    }
  };

  const detectSourceType = (url) => {
    if (url.includes('notion.so')) return 'notion';
    if (url.includes('github.com')) return 'github';
    if (url.includes('docs.google.com')) return 'google-docs';
    return 'website';
  };

  const getSourceIcon = (url) => {
    const type = detectSourceType(url);
    const icons = {
      notion: '📝',
      github: '🐙',
      'google-docs': '📄',
      website: '🌐'
    };
    return icons[type] || '🌐';
  };

  return (
    <div className="url-import-container">
      <form onSubmit={handleSubmit} className="url-import-form">
        <div className="form-group">
          <label htmlFor="url" className="form-label">
            Source URL *
          </label>
          <div className="url-input-container">
            <span className="url-icon">{url ? getSourceIcon(url) : '🌐'}</span>
            <input
              type="url"
              id="url"
              className="form-input url-input"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://notion.so/... or https://github.com/... or any website"
              disabled={importing}
              required
            />
          </div>
          <small className="form-help">
            Supported: Notion pages, GitHub repos, Google Docs, websites, etc.
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="title" className="form-label">
            Title (optional)
          </label>
          <input
            type="text"
            id="title"
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Give your playbook a name"
            disabled={importing}
          />
        </div>

        <div className="form-group">
          <label htmlFor="description" className="form-label">
            Description (optional)
          </label>
          <textarea
            id="description"
            className="form-input form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this playbook contains"
            disabled={importing}
            rows={3}
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-lg import-btn"
          disabled={importing || !url.trim()}
        >
          {importing ? (
            <>
              <span className="spinner"></span>
              Importing...
            </>
          ) : (
            'Import from URL'
          )}
        </button>
      </form>

      <div className="supported-sources">
        <h4>Popular Sources:</h4>
        <div className="source-examples">
          <div className="source-example">
            <span className="source-icon">📝</span>
            <div>
              <strong>Notion</strong>
              <p>Import your company docs and processes</p>
            </div>
          </div>
          <div className="source-example">
            <span className="source-icon">🐙</span>
            <div>
              <strong>GitHub</strong>
              <p>Extract READMEs and documentation</p>
            </div>
          </div>
          <div className="source-example">
            <span className="source-icon">📄</span>
            <div>
              <strong>Google Docs</strong>
              <p>Convert shared documents to playbooks</p>
            </div>
          </div>
          <div className="source-example">
            <span className="source-icon">🌐</span>
            <div>
              <strong>Websites</strong>
              <p>Scrape content from any public page</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default URLImport;
