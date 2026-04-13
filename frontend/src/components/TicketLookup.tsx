"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function TicketLookup() {
  const [ticketId, setTicketId] = useState('');
  const router = useRouter();

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticketId.trim()) {
      router.push(`/ticket/${ticketId.trim()}`);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-xl shadow-indigo-500/5">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-xl flex items-center justify-center text-indigo-600 dark:text-indigo-400">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">Already have a ticket?</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">Enter your ID to track progress.</p>
        </div>
      </div>

      <form onSubmit={handleLookup} className="space-y-4">
        <div className="relative group">
          <input
            type="text"
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value)}
            placeholder="WEB-2026..."
            className="w-full pl-4 pr-4 py-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all dark:text-white placeholder:text-slate-400 font-mono text-sm"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full py-3 px-6 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold hover:bg-slate-800 dark:hover:bg-slate-100 transition-all active:scale-[0.98] shadow-lg shadow-slate-200 dark:shadow-none"
        >
          Check Status
        </button>
      </form>
    </div>
  );
}
