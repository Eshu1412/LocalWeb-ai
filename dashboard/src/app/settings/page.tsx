'use client';

export default function SettingsPage() {
    return (
        <div className="space-y-6 animate-slide-in">
            <div>
                <h1 className="text-3xl font-bold text-white">Settings</h1>
                <p className="text-slate-400 mt-1">Platform configuration and integrations</p>
            </div>

            {/* API Keys */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-4">API Integrations</h2>
                <div className="space-y-4">
                    {[
                        { name: 'OpenAI', key: 'OPENAI_API_KEY', status: true },
                        { name: 'Twilio', key: 'TWILIO_ACCOUNT_SID', status: false },
                        { name: 'Stripe', key: 'STRIPE_SECRET_KEY', status: true },
                        { name: 'WhatsApp', key: 'WHATSAPP_ACCESS_TOKEN', status: false },
                        { name: 'Google Places', key: 'GOOGLE_PLACES_API_KEY', status: true },
                        { name: 'Vercel', key: 'VERCEL_TOKEN', status: false },
                        { name: 'ElevenLabs', key: 'ELEVENLABS_API_KEY', status: false },
                    ].map((api) => (
                        <div key={api.name} className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                            <div className="flex items-center gap-4">
                                <span className={`w-3 h-3 rounded-full ${api.status ? 'bg-green-500' : 'bg-red-500'}`} />
                                <div>
                                    <p className="text-sm font-semibold text-white">{api.name}</p>
                                    <p className="text-xs text-slate-500">{api.key}</p>
                                </div>
                            </div>
                            <button className="px-4 py-2 text-xs bg-brand-500/20 text-brand-400 rounded-lg hover:bg-brand-500/30">
                                Configure
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Feature Flags */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Feature Flags</h2>
                <div className="space-y-4">
                    {[
                        { name: 'Auto Discovery', enabled: false },
                        { name: 'AI Calling', enabled: true },
                        { name: 'WhatsApp Outreach', enabled: true },
                        { name: 'SEO Agent', enabled: true },
                        { name: 'CRM Sync', enabled: true },
                    ].map((flag) => (
                        <div key={flag.name} className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                            <span className="text-sm text-white">{flag.name}</span>
                            <button className={`w-12 h-6 rounded-full transition-colors ${flag.enabled ? 'bg-green-500' : 'bg-slate-600'}`}>
                                <div className={`w-5 h-5 bg-white rounded-full transform transition-transform ${flag.enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Rate Limits */}
            <div className="glass-card p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Rate Limits</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                        { label: 'Discovery', value: '30/min' },
                        { label: 'Calling', value: '50/hour' },
                        { label: 'WhatsApp', value: '200/hour' },
                    ].map((limit) => (
                        <div key={limit.label} className="p-4 rounded-xl bg-white/5 text-center">
                            <p className="text-2xl font-bold text-white">{limit.value}</p>
                            <p className="text-xs text-slate-400 mt-1">{limit.label} Agent</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
