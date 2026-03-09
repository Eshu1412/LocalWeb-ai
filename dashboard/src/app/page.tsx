'use client';

export default function DashboardPage() {
    // Mock data — in production, fetch from /api/pipeline/stats
    const stats = [
        { label: 'Total Leads', value: '2,847', change: '+12%', icon: '👥', color: 'from-blue-500 to-cyan-500' },
        { label: 'Live Sites', value: '184', change: '+8%', icon: '🌐', color: 'from-green-500 to-emerald-500' },
        { label: 'Conversion Rate', value: '6.2%', change: '+1.1%', icon: '📈', color: 'from-purple-500 to-pink-500' },
        { label: 'Monthly Revenue', value: '$12,430', change: '+23%', icon: '💰', color: 'from-amber-500 to-orange-500' },
    ];

    const pipelineStages = [
        { stage: 'Discovered', count: 1247, color: 'bg-slate-500' },
        { stage: 'No Website', count: 892, color: 'bg-blue-500' },
        { stage: 'Sample Ready', count: 456, color: 'bg-cyan-500' },
        { stage: 'Outreach Sent', count: 312, color: 'bg-purple-500' },
        { stage: 'Negotiating', count: 89, color: 'bg-yellow-500' },
        { stage: 'Paid', count: 67, color: 'bg-green-500' },
        { stage: 'Live', count: 184, color: 'bg-emerald-500' },
    ];

    const recentLeads = [
        { name: "Joe's Pizza", category: 'Restaurant', area: 'Brooklyn, NY', status: 'SAMPLE_READY', time: '2m ago' },
        { name: 'Elite Cuts Barbershop', category: 'Barbershop', area: 'Queens, NY', status: 'WHATSAPP_SENT', time: '5m ago' },
        { name: 'Green Leaf Pharmacy', category: 'Pharmacy', area: 'Manhattan, NY', status: 'PAID', time: '12m ago' },
        { name: 'Bright Smile Dental', category: 'Dentist', area: 'Bronx, NY', status: 'CALL_INITIATED', time: '18m ago' },
        { name: 'Sunrise Bakery', category: 'Bakery', area: 'Brooklyn, NY', status: 'LIVE', time: '25m ago' },
    ];

    const statusColors: Record<string, string> = {
        DISCOVERED: 'badge-neutral', NO_WEBSITE: 'badge-info', SAMPLE_READY: 'badge-info',
        WHATSAPP_SENT: 'badge-warning', CALL_INITIATED: 'badge-warning', NEGOTIATING: 'badge-warning',
        PAID: 'badge-success', LIVE: 'badge-success', NOT_INTERESTED: 'badge-danger',
    };

    return (
        <div className="space-y-6 animate-slide-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Pipeline Overview</h1>
                    <p className="text-slate-400 mt-1">Real-time view of your AI sales pipeline</p>
                </div>
                <button className="px-6 py-3 bg-gradient-to-r from-brand-500 to-brand-700 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-brand-500/25 transition-all duration-300 glow">
                    + New Discovery Run
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <div key={stat.label} className="glass-card p-6 hover:scale-[1.02] transition-transform duration-200">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-2xl">{stat.icon}</span>
                            <span className="text-xs font-semibold text-green-400 bg-green-400/10 px-2 py-1 rounded-full">
                                {stat.change}
                            </span>
                        </div>
                        <p className="text-3xl font-bold bg-gradient-to-r {stat.color} bg-clip-text text-transparent">
                            {stat.value}
                        </p>
                        <p className="text-sm text-slate-400 mt-1">{stat.label}</p>
                    </div>
                ))}
            </div>

            {/* Pipeline Funnel */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-6">Pipeline Funnel</h2>
                <div className="flex items-end gap-4 h-48">
                    {pipelineStages.map((stage) => {
                        const maxCount = Math.max(...pipelineStages.map(s => s.count));
                        const height = (stage.count / maxCount) * 100;
                        return (
                            <div key={stage.stage} className="flex-1 flex flex-col items-center gap-2">
                                <span className="text-sm font-bold text-white">{stage.count}</span>
                                <div
                                    className={`w-full ${stage.color} rounded-t-lg transition-all duration-500 hover:opacity-80`}
                                    style={{ height: `${height}%`, minHeight: '20px' }}
                                />
                                <span className="text-xs text-slate-400 text-center">{stage.stage}</span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Recent Leads */}
            <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
                    <a href="/leads" className="text-sm text-brand-500 hover:text-brand-400">View all →</a>
                </div>
                <div className="space-y-3">
                    {recentLeads.map((lead) => (
                        <div
                            key={lead.name}
                            className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors duration-200"
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500/20 to-brand-700/20 flex items-center justify-center text-brand-400 font-bold">
                                    {lead.name[0]}
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-white">{lead.name}</p>
                                    <p className="text-xs text-slate-400">{lead.category} · {lead.area}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-4">
                                <span className={`badge ${statusColors[lead.status] || 'badge-neutral'}`}>
                                    {lead.status.replace(/_/g, ' ')}
                                </span>
                                <span className="text-xs text-slate-500">{lead.time}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
