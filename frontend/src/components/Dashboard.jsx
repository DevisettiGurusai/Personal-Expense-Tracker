import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { TrendingUp, Wallet, ArrowDownCircle, ArrowUpCircle, Sparkles } from 'lucide-react';

const COLORS = ['#38bdf8', '#818cf8', '#c084fc', '#fb7185', '#fb923c', '#facc15', '#4ade80'];

export default function Dashboard({ apiBase }) {
  const [statements, setStatements] = useState([]);
  const [selected, setSelected] = useState([]);
  const [data, setData] = useState(null);
  const [advice, setAdvice] = useState('');
  const [adviceLoading, setAdviceLoading] = useState(false);

  useEffect(() => {
    fetchStatements();
  }, []);

  const fetchStatements = async () => {
    const res = await axios.get(`${apiBase}/statements`);
    setStatements(res.data.statements);
  };

  const fetchDashboardData = async (selectedList) => {
    const res = await axios.post(`${apiBase}/dashboard`, { selected_statements: selectedList });
    setData(res.data);
  };

  const toggleStatement = (name) => {
    const newList = selected.includes(name)
      ? selected.filter(s => s !== name)
      : [...selected, name];
    setSelected(newList);
    fetchDashboardData(newList);
  };

  const getAdvice = async () => {
    if (!data) return;
    setAdviceLoading(true);
    try {
      const currency = data.summary.currency || "$";
      const summaryText = `Income: ${currency}${data.summary.total_income}, Expenses: ${currency}${data.summary.total_expenses}. Categories: ${JSON.stringify(data.charts.categories)}`;
      const res = await axios.post(`${apiBase}/advice`, { summary_text: summaryText });
      setAdvice(res.data.advice);
    } catch (err) {
      console.error(err);
    } finally {
      setAdviceLoading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="glass-card" style={{ marginBottom: '32px' }}>
        <h3 style={{ marginBottom: '16px' }}>📂 Select Statements</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {statements.map(s => (
            <button
              key={s}
              className={`btn ${selected.includes(s) ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => toggleStatement(s)}
            >
              {s}
            </button>
          ))}
          {statements.length === 0 && <p style={{ color: 'var(--text-secondary)' }}>No statements found. Upload some first!</p>}
        </div>
      </div>

      {data && data.summary && (
        <>
          <div className="grid-cols-3 animate-fade-in" style={{ marginBottom: '32px' }}>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>TOTAL INCOME</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--accent-income)' }}>
                {data.summary.currency}{data.summary.total_income.toLocaleString()}
              </div>
            </div>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>TOTAL EXPENSES</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--accent-expense)' }}>
                {data.summary.currency}{data.summary.total_expenses.toLocaleString()}
              </div>
            </div>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>NET BALANCE</div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: data.summary.net_balance >= 0 ? 'var(--accent-income)' : 'var(--accent-expense)' }}>
                {data.summary.currency}{data.summary.net_balance.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="grid-cols-3" style={{ gridTemplateColumns: '1fr 2fr', gap: '32px', marginBottom: '32px' }}>
            <div className="glass-card">
              <h3 style={{ marginBottom: '20px' }}>Expense Categories</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.charts.categories}
                      dataKey="Amount"
                      nameKey="Category"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                    >
                      {data.charts.categories.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: 'white' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card">
              <h3 style={{ marginBottom: '20px' }}>Spending Trend</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.charts.trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="Month" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: 'white' }} />
                    <Line type="monotone" dataKey="Amount" stroke="var(--accent-expense)" strokeWidth={3} dot={{ fill: 'var(--accent-expense)', r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="glass-card" style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>💡 AI Financial Advisor</h3>
              <button className="btn btn-primary" onClick={getAdvice} disabled={adviceLoading}>
                {adviceLoading ? "Thinking..." : <><Sparkles size={18} /> Get Tips</>}
              </button>
            </div>
            {advice && (
              <div className="animate-fade-in" style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                {advice}
              </div>
            )}
          </div>

          <div className="glass-card">
            <h3 style={{ marginBottom: '20px' }}>📋 Transaction History</h3>
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Merchant</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data.transactions.map((t, idx) => (
                    <tr key={idx}>
                      <td>{t.Date}</td>
                      <td>{t.Merchant}</td>
                      <td><span style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>{t.Category}</span></td>
                      <td style={{ color: t.Type.toUpperCase() === 'DEBIT' ? 'var(--accent-expense)' : 'var(--accent-income)' }}>{t.Type}</td>
                      <td style={{ fontWeight: 'bold' }}>{t.Currency}{t.Amount.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
