import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_playbooks: 0,
    active_projects: 0,
    total_collaborators: 0,
    storage_used: "0 MB"
  });
  const [recentPlaybooks, setRecentPlaybooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch('/api/dashboard/stats');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
      
      // Fetch recent playbooks
      const recentResponse = await fetch('/api/dashboard/recent');
      if (recentResponse.ok) {
        const recentData = await recentResponse.json();
        setRecentPlaybooks(recentData.playbooks || []);
      }
      
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'processing': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

const Dashboard = () => {
  const recentPlaybooks = [
    {
      id: '1',
      title: 'Startup GTM Strategy',
      description: 'Complete go-to-market playbook for early-stage startups',
      lastUpdated: '2 hours ago',
      author: 'Jane Smith',
      blocks: 24,
      status: 'published'
    },
    {
      id: '2',
      title: 'Engineering Hiring Process',
      description: 'End-to-end hiring workflow for technical roles',
      lastUpdated: '1 day ago',
      author: 'John Doe',
      blocks: 18,
      status: 'draft'
    }
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Welcome to PlaybookOS</h1>
          <p>Your collaborative platform for business playbooks</p>
        </div>
        <Link to="/upload" className="btn btn-primary btn-lg">
          + Import Playbook
        </Link>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-number">12</div>
          <div className="stat-label">Playbooks</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">8</div>
          <div className="stat-label">Contributors</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">246</div>
          <div className="stat-label">Content Blocks</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">15</div>
          <div className="stat-label">Pull Requests</div>
        </div>
      </div>

      <div className="dashboard-content">
        <section className="recent-playbooks">
          <div className="section-header">
            <h2>Recent Playbooks</h2>
            <Link to="/playbooks" className="btn btn-secondary">View All</Link>
          </div>
          
          <div className="playbooks-grid">
            {recentPlaybooks.map((playbook) => (
              <div key={playbook.id} className="playbook-card">
                <div className="card-header">
                  <div className="playbook-title">
                    <Link to={`/playbook/${playbook.id}`}>{playbook.title}</Link>
                  </div>
                  <span className={`status-badge ${playbook.status}`}>
                    {playbook.status}
                  </span>
                </div>
                <div className="card-body">
                  <p className="playbook-description">{playbook.description}</p>
                  <div className="playbook-meta">
                    <div className="meta-item">
                      <span className="meta-icon">👤</span>
                      {playbook.author}
                    </div>
                    <div className="meta-item">
                      <span className="meta-icon">📄</span>
                      {playbook.blocks} blocks
                    </div>
                    <div className="meta-item">
                      <span className="meta-icon">🕒</span>
                      {playbook.lastUpdated}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <Link to="/upload" className="action-card">
              <div className="action-icon">📁</div>
              <h3>Import Playbook</h3>
              <p>Upload files or import from external sources</p>
            </Link>
            <div className="action-card">
              <div className="action-icon">✨</div>
              <h3>Create from Template</h3>
              <p>Start with a proven playbook template</p>
            </div>
            <div className="action-card">
              <div className="action-icon">🔍</div>
              <h3>Browse Community</h3>
              <p>Discover playbooks shared by other founders</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
