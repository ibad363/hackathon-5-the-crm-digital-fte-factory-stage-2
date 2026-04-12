"use client";

import React, { useState } from 'react';

const CATEGORIES = [
  { value: 'general', label: 'General Question' },
  { value: 'technical', label: 'Technical Support' },
  { value: 'billing', label: 'Billing Inquiry' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feedback', label: 'Feedback' }
];

const PRIORITIES = [
  { value: 'low', label: 'Low - Not urgent' },
  { value: 'medium', label: 'Medium - Need help soon' },
  { value: 'high', label: 'High - Urgent issue' }
];

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

type Status = 'idle' | 'submitting' | 'success' | 'error';

interface SupportFormProps {
  apiEndpoint?: string;
}

export default function SupportForm({ apiEndpoint = '/api/support/submit' }: SupportFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    category: 'general',
    priority: 'medium',
    message: ''
  });

  const [status, setStatus] = useState<Status>('idle');
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validateForm = (): boolean => {
    if (formData.name.trim().length < 2) {
      setError('Please enter your name (at least 2 characters)');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (formData.subject.trim().length < 5) {
      setError('Please enter a subject (at least 5 characters)');
      return false;
    }
    if (formData.message.trim().length < 10) {
      setError('Please describe your issue in more detail (at least 10 characters)');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setStatus('submitting');

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Submission failed');
      }

      const data = await response.json();
      setTicketId(data.ticket_id);
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="max-w-2xl mx-auto p-8 glass rounded-3xl animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="text-center">
          <div className="w-20 h-20 bg-green-500/10 dark:bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-green-500/30">
            <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">Request Received!</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-8 max-w-sm mx-auto">
            Our AI engine is already analyzing your request. You'll receive an email shortly.
          </p>

          <div className="bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 mb-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
               <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24"><path d="M15 5v2h3v11h-3v2h5V5h-5zm-3 2l-5 5 5 5v-3h5v-4h-5V7z"/></svg>
            </div>
            <p className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest mb-1">Support Ticket ID</p>
            <p className="text-2xl font-mono font-bold text-slate-900 dark:text-white tracking-tight">{ticketId}</p>
          </div>

          <button
            onClick={() => {
              setStatus('idle');
              setFormData({ name: '', email: '', subject: '', category: 'general', priority: 'medium', message: '' });
            }}
            className="px-8 py-3 bg-indigo-600 text-white rounded-full font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 transition-all hover:scale-105 active:scale-95"
          >
            Submit Another Request
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-8 glass rounded-3xl shadow-2xl shadow-indigo-500/5">
      <div className="flex items-center space-x-3 mb-2">
        <div className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse"></div>
        <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest">Live Support Portal</span>
      </div>
      <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">How can we help?</h2>
      <p className="text-slate-600 dark:text-slate-400 mb-8">
        Describe your issue and our AI agents will provide an expert resolution in minutes.
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-600 dark:text-red-400 text-sm font-medium flex items-center">
          <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Name Field */}
          <div className="relative group">
            <label htmlFor="name" className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 group-focus-within:text-indigo-600 transition-colors">
              Full Name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white placeholder:text-slate-400"
                placeholder="John Doe"
              />
            </div>
          </div>

          {/* Email Field */}
          <div className="relative group">
            <label htmlFor="email" className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 group-focus-within:text-indigo-600 transition-colors">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white placeholder:text-slate-400"
                placeholder="john@example.com"
              />
            </div>
          </div>
        </div>

        {/* Subject Field */}
        <div className="relative group">
          <label htmlFor="subject" className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 group-focus-within:text-indigo-600 transition-colors">
            Topic / Subject
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-500 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              required
              className="w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white placeholder:text-slate-400"
              placeholder="What do you need help with?"
            />
          </div>
        </div>

        {/* Category and Priority Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="group">
            <label htmlFor="category" className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 group-focus-within:text-indigo-600 transition-colors">
              Inquiry Category
            </label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white cursor-pointer appearance-none"
              style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%2394a3b8\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\'%3E%3C/path%3E%3C/svg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center', backgroundSize: '1.25rem' }}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>

          <div className="group">
            <label htmlFor="priority" className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 group-focus-within:text-indigo-600 transition-colors">
              Urgency Level
            </label>
            <select
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white cursor-pointer appearance-none"
              style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%2394a3b8\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\'%3E%3C/path%3E%3C/svg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center', backgroundSize: '1.25rem' }}
            >
              {PRIORITIES.map(pri => (
                <option key={pri.value} value={pri.value}>{pri.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Message Field */}
        <div className="group">
          <label htmlFor="message" className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 group-focus-within:text-indigo-600 transition-colors">
            Detailed Description
          </label>
          <textarea
            id="message"
            name="message"
            value={formData.message}
            onChange={handleChange}
            required
            rows={5}
            maxLength={1000}
            className="w-full px-4 py-3 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white placeholder:text-slate-400 resize-none"
            placeholder="Tell us more about what's happening..."
          />
          <div className="mt-2 flex justify-between items-center">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">AI Analysis Active</p>
            <p className="text-xs text-slate-400 font-medium">
              {formData.message.length}/1000
            </p>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={status === 'submitting'}
          className={`group w-full py-4 px-6 rounded-xl font-bold text-white transition-all shadow-xl hover:shadow-indigo-500/20 active:scale-[0.98] ${
            status === 'submitting'
              ? 'bg-slate-400 cursor-not-allowed opacity-50'
              : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {status === 'submitting' ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Analyzing Request...
            </span>
          ) : (
            <span className="flex items-center justify-center">
              Submit Support Request
              <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </span>
          )}
        </button>

        <p className="text-center text-[10px] text-slate-400 font-bold uppercase tracking-widest">
          Secure AI Encryption · GDPR Compliant
        </p>
      </form>
    </div>
  );
}
