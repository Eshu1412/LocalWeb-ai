'use client';

export default function AgentsPage() {
    const agents = [
        { name: 'Discovery Agent', status: 'running', queue: 0, processed: 1247, errors: 2, icon: '🔍' },
        { name: 'Verification Agent', status: 'running', queue: 3, processed: 1180, errors: 5, icon: '✅' },
        { name: 'Sample Builder', status: 'running', queue: 12, processed: 892, errors: 8, icon: '🏗️' },
        { name: 'Calling Agent', status: 'paused', queue: 0, processed: 456, errors: 12, icon: '📞' },
        { name: 'WhatsApp Agent', status: 'running', queue: 5, processed: 723, errors: 3, icon: '💬' },
        { name: 'Negotiation Agent', status: 'running', queue: 2, processed: 312, errors: 1, icon: '🤝' },
        { name: 'Payment Agent', status: 'running', queue: 0, processed: 89, errors: 0, icon: '💳' },
        { name: 'Builder Agent', status: 'running', queue: 4, processed: 67, errors: 2, icon: '🔨' },
        { name: 'QA Agent', status: 'running', queue: 1, processed: 65, errors: 0, icon: '🧪' },
        { name: 'SEO Agent', status: 'running', queue: 0, processed: 184, errors: 0, icon: '📊' },
        { name: 'CRM Agent', status: 'running', queue: 0, processed: 184, errors: 0, icon: '📋' },
        { name: 'Orchestrator', status: 'running', queue: 0, processed: 2847, errors: 1, icon: '🎯' },
    ];

    return (
        <div className="space-y-6 animate-slide-in">
            <div>
                <h1 className="text-3xl font-bold text-white">Agent Control</h1>
                <p className="text-slate-400 mt-1">Monitor and manage all AI agents</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents.map((agent) => (
                    <div key={agent.name} className="glass-card p-6 hover:scale-[1.01] transition-transform">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">{agent.icon}</span>
                                <h3 className="font-semibold text-white">{agent.name}</h3>
                            </div>
                            <span className={`w-3 h-3 rounded-full ${agent.status === 'running' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                        </div>
                        <div className="grid grid-cols-3 gap-4 mb-4">
                            <div>
                                <p className="text-2xl font-bold text-white">{agent.processed}</p>
                                <p className="text-xs text-slate-400">Processed</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-cyan-400">{agent.queue}</p>
                                <p className="text-xs text-slate-400">In Queue</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-red-400">{agent.errors}</p>
                                <p className="text-xs text-slate-400">Errors</p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button className={`flex-1 px-3 py-2 text-xs rounded-lg font-medium ${agent.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-green-500/20 text-green-400'}`}>
                                {agent.status === 'running' ? '⏸ Pause' : '▶ Resume'}
                            </button>
                            <button className="flex-1 px-3 py-2 text-xs bg-red-500/20 text-red-400 rounded-lg font-medium">⏹ Stop</button>
                            <button className="flex-1 px-3 py-2 text-xs bg-blue-500/20 text-blue-400 rounded-lg font-medium">🔄 Restart</button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
