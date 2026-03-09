import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'LocalWeb AI — Admin Dashboard',
    description: 'Automated AI Agent Platform for Local Business Websites',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className="dark">
            <body className="min-h-screen bg-surface-950">
                <div className="flex min-h-screen">
                    {/* Sidebar */}
                    <aside className="w-64 glass-card m-3 mr-0 p-6 flex flex-col gap-2 fixed h-[calc(100vh-24px)]">
                        <div className="flex items-center gap-3 mb-8">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold text-lg glow">
                                L
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-white">LocalWeb AI</h1>
                                <p className="text-xs text-slate-400">Admin Dashboard</p>
                            </div>
                        </div>

                        <nav className="flex flex-col gap-1">
                            {[
                                { name: 'Pipeline', href: '/', icon: '📊' },
                                { name: 'Leads', href: '/leads', icon: '👥' },
                                { name: 'Analytics', href: '/analytics', icon: '📈' },
                                { name: 'Agents', href: '/agents', icon: '🤖' },
                                { name: 'Sites', href: '/sites', icon: '🌐' },
                                { name: 'Templates', href: '/templates', icon: '🎨' },
                                { name: 'Settings', href: '/settings', icon: '⚙️' },
                            ].map((item) => (
                                <a
                                    key={item.name}
                                    href={item.href}
                                    className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-all duration-200"
                                >
                                    <span className="text-lg">{item.icon}</span>
                                    {item.name}
                                </a>
                            ))}
                        </nav>

                        <div className="mt-auto pt-4 border-t border-slate-700/50">
                            <div className="flex items-center gap-3 px-4 py-2">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-emerald-600" />
                                <div>
                                    <p className="text-sm font-medium text-white">Admin</p>
                                    <p className="text-xs text-slate-400">super_admin</p>
                                </div>
                            </div>
                        </div>
                    </aside>

                    {/* Main Content */}
                    <main className="ml-[280px] flex-1 p-6">
                        {children}
                    </main>
                </div>
            </body>
        </html>
    );
}
