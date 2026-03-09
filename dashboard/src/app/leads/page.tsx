'use client';

export default function LeadsPage() {
    const leads = [
        { id: '1', name: "Joe's Pizza", phone: '+1234567890', category: 'Restaurant', area: 'Brooklyn, NY', status: 'SAMPLE_READY', source: 'google_places', created: '2024-03-08' },
        { id: '2', name: 'Elite Cuts', phone: '+1234567891', category: 'Barbershop', area: 'Queens, NY', status: 'WHATSAPP_SENT', source: 'google_places', created: '2024-03-08' },
        { id: '3', name: 'Green Leaf Pharmacy', phone: '+1234567892', category: 'Pharmacy', area: 'Manhattan, NY', status: 'PAID', source: 'yelp', created: '2024-03-07' },
        { id: '4', name: 'Bright Smile Dental', phone: '+1234567893', category: 'Dentist', area: 'Bronx, NY', status: 'LIVE', source: 'google_places', created: '2024-03-07' },
        { id: '5', name: 'Fresh Fit Gym', phone: '+1234567894', category: 'Gym', area: 'Brooklyn, NY', status: 'NEGOTIATING', source: 'google_places', created: '2024-03-06' },
    ];

    const statusColors: Record<string, string> = {
        DISCOVERED: 'badge-neutral', NO_WEBSITE: 'badge-info', SAMPLE_READY: 'badge-info',
        WHATSAPP_SENT: 'badge-warning', CALL_INITIATED: 'badge-warning', NEGOTIATING: 'badge-warning',
        PAID: 'badge-success', LIVE: 'badge-success', NOT_INTERESTED: 'badge-danger',
    };

    return (
        <div className="space-y-6 animate-slide-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Leads</h1>
                    <p className="text-slate-400 mt-1">Manage and track all discovered businesses</p>
                </div>
                <div className="flex gap-3">
                    <input
                        type="text" placeholder="Search leads..."
                        className="px-4 py-2 bg-white/5 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
                    />
                    <select className="px-4 py-2 bg-white/5 border border-slate-700 rounded-xl text-sm text-slate-300">
                        <option value="">All Statuses</option>
                        <option>DISCOVERED</option><option>NO_WEBSITE</option>
                        <option>SAMPLE_READY</option><option>PAID</option><option>LIVE</option>
                    </select>
                </div>
            </div>

            <div className="glass-card overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-slate-700/50">
                            {['Business', 'Category', 'Area', 'Status', 'Source', 'Date', 'Actions'].map(h => (
                                <th key={h} className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {leads.map((lead) => (
                            <tr key={lead.id} className="border-b border-slate-700/30 hover:bg-white/5 transition-colors">
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500/30 to-brand-700/30 flex items-center justify-center text-brand-400 font-bold text-sm">{lead.name[0]}</div>
                                        <div>
                                            <p className="text-sm font-semibold text-white">{lead.name}</p>
                                            <p className="text-xs text-slate-500">{lead.phone}</p>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-slate-300">{lead.category}</td>
                                <td className="px-6 py-4 text-sm text-slate-300">{lead.area}</td>
                                <td className="px-6 py-4"><span className={`badge ${statusColors[lead.status]}`}>{lead.status.replace(/_/g, ' ')}</span></td>
                                <td className="px-6 py-4 text-sm text-slate-400">{lead.source}</td>
                                <td className="px-6 py-4 text-sm text-slate-400">{lead.created}</td>
                                <td className="px-6 py-4">
                                    <div className="flex gap-2">
                                        <button className="px-3 py-1 text-xs bg-brand-500/20 text-brand-400 rounded-lg hover:bg-brand-500/30">📞 Call</button>
                                        <button className="px-3 py-1 text-xs bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30">💬 WhatsApp</button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
