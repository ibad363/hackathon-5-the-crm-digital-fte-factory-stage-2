import SupportForm from "@/components/SupportForm";
import TicketLookup from "@/components/TicketLookup";

export default function Home() {
  return (
    <div className="flex flex-col w-full">
      {/* Hero Section */}
      <section className="pt-16 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-6">
            Help that never <span className="text-indigo-600 dark:text-indigo-400">sleeps.</span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Our autonomous AI agents are ready to resolve your issues instantly, 24/7.
            Experience the future of customer success today.
          </p>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto text-left">
            <div className="md:col-span-1">
              <TicketLookup />
            </div>
            <div className="grid grid-cols-1 gap-4">
              <div className="glass-card p-6 flex items-center space-x-4 h-full">
                <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 rounded-xl flex items-center justify-center text-indigo-600 dark:text-indigo-400 shrink-0">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">5 mins</div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Avg Response Time</div>
                </div>
              </div>
              <div className="glass-card p-6 flex items-center space-x-4 h-full">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center text-green-600 dark:text-green-400 shrink-0">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">98%</div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Auto-Resolution Rate</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Support Portal */}
      <section id="support-form" className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-100/50 dark:bg-slate-900/20 border-y border-slate-200/50 dark:border-slate-800/50">
        <div className="max-w-4xl mx-auto">
          <SupportForm apiEndpoint="/api/support/submit" />
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-slate-900 dark:text-white mb-12">How AI Support Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-4 font-bold">1</div>
              <h3 className="font-bold text-lg mb-2">Instant Intake</h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm">Submit your request via web, email, or WhatsApp. Our system ingests it immediately.</p>
            </div>
            <div className="flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-violet-100 dark:bg-violet-900/30 rounded-full flex items-center justify-center text-violet-600 dark:text-violet-400 mb-4 font-bold">2</div>
              <h3 className="font-bold text-lg mb-2">Deep Analysis</h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm">Our AI analyzes your issue against our vast knowledge base and your history.</p>
            </div>
            <div className="flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 mb-4 font-bold">3</div>
              <h3 className="font-bold text-lg mb-2">Expert Resolution</h3>
              <p className="text-slate-600 dark:text-slate-400 text-sm">You get a tailored response or solution in minutes, or it's escalated to a human expert.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
