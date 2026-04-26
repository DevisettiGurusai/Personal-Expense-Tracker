import React, { useState } from 'react';
import axios from 'axios';
import { Upload, Save, CheckCircle2, Sparkles, Loader2 } from 'lucide-react';

export default function Uploader({ apiBase }) {
  const [files, setFiles] = useState([]);
  const [statementName, setStatementName] = useState('');
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleUpload = async () => {
    if (!statementName) return alert("Please name this statement!");
    if (files.length === 0) return alert("Please select files first!");

    setLoading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const res = await axios.post(`${apiBase}/upload`, formData);
      setExtractedData(res.data.transactions);
    } catch (err) {
      alert("Extraction failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await axios.post(`${apiBase}/save`, {
        statement_name: statementName,
        transactions: extractedData
      });
      setSuccess("Successfully saved to database!");
      setExtractedData(null);
      setFiles([]);
      setStatementName('');
    } catch (err) {
      alert("Save failed: " + (err.response?.data?.detail || err.message));
    }
  };

  const updateRow = (index, field, value) => {
    const newData = [...extractedData];
    newData[index][field] = value;
    setExtractedData(newData);
  };

  return (
    <div className="animate-fade-in">
      <div className="glass-card" style={{ marginBottom: '32px' }}>
        <h2 style={{ marginBottom: '20px' }}>📤 Process New Statements</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '8px' }}>Statement Name</label>
            <input 
              type="text" 
              placeholder="e.g. June 2024 Bank Statement"
              value={statementName}
              onChange={(e) => setStatementName(e.target.value)}
              style={{ width: '100%', padding: '12px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '8px' }}>Select PDF or Images</label>
            <input 
              type="file" 
              multiple 
              onChange={(e) => setFiles(e.target.files)}
              className="btn btn-outline"
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <button 
          className="btn btn-primary" 
          onClick={handleUpload} 
          disabled={loading}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {loading ? <Loader2 className="spin" /> : <Sparkles size={18} />}
          {loading ? "AI is Analyzing..." : "Extract Transactions"}
        </button>
      </div>

      {success && (
        <div className="glass-card flex-center" style={{ marginBottom: '32px', borderColor: 'var(--accent-income)' }}>
          <CheckCircle2 color="var(--accent-income)" style={{ marginRight: '12px' }} />
          <p>{success}</p>
        </div>
      )}

      {extractedData && (
        <div className="glass-card animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>🔍 Review & Edit Transactions</h3>
            <button className="btn btn-primary" onClick={handleSave}>
              <Save size={18} /> Save to Database
            </button>
          </div>
          
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Merchant</th>
                  <th>Amount</th>
                  <th>Curr</th>
                  <th>Category</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {extractedData.map((row, idx) => (
                  <tr key={idx}>
                    <td><input type="text" value={row.Date} onChange={(e) => updateRow(idx, 'Date', e.target.value)} /></td>
                    <td><input type="text" value={row.Merchant} onChange={(e) => updateRow(idx, 'Merchant', e.target.value)} /></td>
                    <td><input type="number" value={row.Amount} onChange={(e) => updateRow(idx, 'Amount', parseFloat(e.target.value))} /></td>
                    <td><input type="text" value={row.Currency} onChange={(e) => updateRow(idx, 'Currency', e.target.value)} style={{ width: '40px', textAlign: 'center' }} /></td>
                    <td>
                      <select value={row.Category} onChange={(e) => updateRow(idx, 'Category', e.target.value)}>
                        <option>Food & Dining</option>
                        <option>Groceries</option>
                        <option>Transport & Auto</option>
                        <option>Utilities</option>
                        <option>Shopping</option>
                        <option>Entertainment</option>
                        <option>Income/Refunds</option>
                        <option>Other</option>
                      </select>
                    </td>
                    <td>
                      <select value={row.Type} onChange={(e) => updateRow(idx, 'Type', e.target.value)}>
                        <option>Debit</option>
                        <option>Credit</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <style dangerouslySetInnerHTML={{ __html: `
        .spin { animation: rotate 1s linear infinite; }
        @keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}} />
    </div>
  );
}
