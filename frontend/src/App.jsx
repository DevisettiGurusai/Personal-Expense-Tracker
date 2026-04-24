import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout, Upload, BarChart3, PieChart as PieChartIcon, Save, Sparkles, Plus, Search, CheckCircle2, AlertCircle } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Uploader from './components/Uploader';

const API_BASE = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [isAiOk, setIsAiOk] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/health`)
      .then(res => setIsAiOk(res.data.ai_configured))
      .catch(err => console.error("Server connection failed", err));
  }, []);

  return (
    <div className="container animate-fade-in">
      <header className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '40px' }}>
        <div>
          <h1 style={{ fontSize: '32px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '40px' }}>💸</span> Expense Tracker
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Next-Gen AI Financial Assistant</p>
        </div>
        <div className="flex-center" style={{ gap: '20px' }}>
          <button 
            className={`btn ${activeTab === 'upload' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('upload')}
          >
            <Upload size={18} /> Upload
          </button>
          <button 
            className={`btn ${activeTab === 'dashboard' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart3 size={18} /> Dashboard
          </button>
        </div>
      </header>

      {!isAiOk && (
        <div className="glass-card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--accent-expense)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertCircle color="var(--accent-expense)" />
            <p><strong>API Warning:</strong> Your GROQ_API_KEY is not configured in the backend .env file.</p>
          </div>
        </div>
      )}

      <main>
        {activeTab === 'upload' ? <Uploader apiBase={API_BASE} /> : <Dashboard apiBase={API_BASE} />}
      </main>

      <footer style={{ marginTop: '60px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '14px' }}>
        Built with React, FastAPI & Groq AI
      </footer>
    </div>
  );
}

export default App;
