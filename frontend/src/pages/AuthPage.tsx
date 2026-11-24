import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const AuthPage: React.FC<{ mode: 'login' | 'signup' }> = ({ mode }) => {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await signup(email, fullName, password);
      }
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Authentication error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="card auth-card">
        <h2>{mode === 'login' ? 'Campus Event Portal Login' : 'Create Student / Organizer Account'}</h2>
        {error && <div className="alert error">{error}</div>}
        <form onSubmit={handleSubmit} className="stack">
          {mode === 'signup' && (
            <input
              type="text"
              placeholder="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          )}
          <input
            type="email"
            placeholder="University Email (e.g. alice@campus.edu)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password (min 6 chars)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" className="btn primary" disabled={submitting}>
            {submitting ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Sign Up'}
          </button>
        </form>
        <p className="muted" style={{ marginTop: '1rem' }}>
          {mode === 'login' ? (
            <>
              Don&apos;t have an account? <a href="/signup">Register here</a>
            </>
          ) : (
            <>
              Already registered? <a href="/login">Sign in</a>
            </>
          )}
        </p>
      </div>
    </div>
  );
};