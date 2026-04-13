"use client";

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';

interface Message {
  role: 'customer' | 'agent' | 'system';
  content: string;
  created_at: string;
  direction: 'inbound' | 'outbound';
}

interface TicketData {
  ticket_id: string;
  status: string;
  created_at: string;
  category: string;
  priority: string;
  messages: Message[];
}

export default function TicketStatusPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [ticket, setTicket] = useState<TicketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      // Direct call to Next.js API proxy (we'll create this next)
      const response = await fetch(`/api/support/ticket/${id}`);

      if (!response.ok) {
        if (response.status === 404) throw new Error("Ticket not found");
        throw new Error("Failed to load ticket details");
      }

      const data = await response.json();
      setTicket(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Poll every 10 seconds while ticket is not resolved/escalated
    const interval = setInterval(() => {
      if (ticket && (ticket.status === 'open' || ticket.status === 'active')) {
        fetchStatus();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [id, ticket?.status]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading ticket details...</p>
        </div>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-8 text-center">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Error</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{error || "Could not find your ticket."}</p>
          <Link href="/" className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors font-medium">
            Go Back Home
          </Link>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'active': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'resolved': return 'bg-green-100 text-green-700 border-green-200';
      case 'escalated': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Header Info */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Ticket Status</h1>
            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(ticket.status)}`}>
              {ticket.status.toUpperCase()}
            </span>
          </div>
          <p className="text-sm text-slate-500 font-mono">{ticket.ticket_id}</p>
        </div>

        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
            <p className="text-slate-400 uppercase tracking-wider font-semibold mb-1">Category</p>
            <p className="text-slate-900 dark:text-white font-medium capitalize">{ticket.category}</p>
          </div>
          <div className="bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
            <p className="text-slate-400 uppercase tracking-wider font-semibold mb-1">Priority</p>
            <p className="text-slate-900 dark:text-white font-medium capitalize">{ticket.priority}</p>
          </div>
        </div>
      </div>

      {/* Conversation History */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 flex flex-col min-h-[400px]">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <h2 className="font-bold text-slate-900 dark:text-white">Activity Log</h2>
          <button
            onClick={fetchStatus}
            className="p-2 text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors"
            title="Refresh"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        <div className="flex-1 p-4 sm:p-6 space-y-6 overflow-y-auto">
          {ticket.messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'customer' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 ${
                msg.role === 'customer'
                  ? 'bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-200 dark:shadow-none'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-tl-none border border-slate-200 dark:border-slate-700'
              }`}>
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-[10px] uppercase font-bold opacity-70 tracking-tight">
                    {msg.role === 'agent' ? '🤖 TaskVault AI' : msg.role === 'customer' ? '👤 You' : '⚙️ System'}
                  </span>
                  <span className="text-[10px] opacity-50">•</span>
                  <span className="text-[10px] opacity-60">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>
              </div>
            </div>
          ))}

          {ticket.status === 'open' && (
            <div className="flex justify-start">
              <div className="bg-slate-50 dark:bg-slate-800/30 border border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-4 flex items-center space-x-3 text-slate-500 animate-pulse w-full max-w-[200px]">
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
                <span className="text-xs font-medium italic">Agent thinking...</span>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 bg-slate-50 dark:bg-slate-800/20 border-t border-slate-100 dark:border-slate-800 rounded-b-2xl">
          <p className="text-xs text-center text-slate-500 dark:text-slate-400">
            {ticket.status === 'resolved'
              ? "This ticket has been marked as resolved. Check your email for full details."
              : ticket.status === 'escalated'
              ? "Your request was escalated to a human specialist. They will email you shortly."
              : "Our AI is currently reviewing your request. This page updates automatically."}
          </p>
        </div>
      </div>

      <div className="text-center">
        <Link href="/" className="text-sm font-medium text-indigo-600 hover:text-indigo-500 flex items-center justify-center space-x-1 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Help Center</span>
        </Link>
      </div>
    </div>
  );
}
