'use client';

export default function AnalyticsPage() {
    const metrics = [
        { label: 'Lead-to-Contact Rate', value: '72%', target: '70%', status: 'above' },
        { label: 'Contact-to-Interested', value: '18%', target: '15%', status: 'above' },
        { label: 'Interested-to-Paid', value: '43%', target: '40%', status: 'above' },
        { label: 'Overall Conversion', value: '6.2%', target: '5%', status: 'above' },
        { label: 'MRR Growth', value: '23%', target: '20%', status: 'above' },
        { label: 'Monthly Churn', value: '2.1%', target: '<3%', status: 'above' },
    ];

    const unitEconomics = [
        { item: 'Cost per lead discovered', cost: '$0.002' },
        { item: 'Cost per verification', cost: '$0.001' },
        { item: 'Cost per sample site', cost: '$0.15' },
        { item: 'Cost per AI call (60s)', cost: '$0.08' },
        { item: 'Cost per WhatsApp sequence', cost: '$0.03' },
        { item: 'Cost per site deploy', cost: '$0.50' },
        { item: 'Total cost per conversion', cost: '$2-5' },
        { item: 'LTV (18mo avg @ $49/mo)', cost: '$882' },
        { item: 'LTV:CAC Ratio', cost: '~176:1' },
    ];

    return (
        <div className="space-y-6 animate-slide-in">
            <div>
                <h1 className="text-3xl font-bold text-white">Analytics</h1>
                <p className="text-slate-400 mt-1">Key performance metrics and unit economics</p>
            </div>

            {/* KPI Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {metrics.map((m) => (
                    <div key={m.label} className="glass-card p-6">
                        <p className="text-sm text-slate-400 mb-2">{m.label}</p>
                        <div className="flex items-end gap-3">
                            <span className="text-4xl font-bold text-white">{m.value}</span>
                            <span className="text-sm text-green-400 mb-1">✓ Target: {m.target}</span>
                        </div>
                        <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-brand-500 to-green-500 rounded-full" style={{ width: m.value }} />
                        </div>
                    </div>
                ))}
            </div>

            {/* Unit Economics */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-6">Unit Economics</h2>
                <div className="space-y-3">
                    {unitEconomics.map((item) => (
                        <div key={item.item} className="flex items-center justify-between py-3 border-b border-slate-700/30 last:border-0">
                            <span className="text-sm text-slate-300">{item.item}</span>
                            <span className="text-sm font-bold text-white">{item.cost}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
