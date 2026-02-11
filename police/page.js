'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Shield,
    Siren,
    MapPin,
    Radio,
    Bell,
    Clock,
    CheckCircle,
    AlertTriangle,
    Users,
    Activity,
    Phone
} from 'lucide-react';

export default function PoliceDashboard() {
    const [activeAlerts, setActiveAlerts] = useState([
        {
            id: 1,
            type: 'SOS Emergency',
            location: 'Central Park, Near Boat House, NY',
            time: 'Just now',
            details: 'Panic button activated by user. Location tracking enabled. Ambient audio recording started.',
            priority: 'High',
            status: 'Active'
        },
        {
            id: 2,
            type: 'Voice Distress',
            location: '5th Avenue & 42nd St',
            time: '3 mins ago',
            details: 'High-decibel scream detected followed by "Help". AI confidence score: 98%.',
            priority: 'Critical',
            status: 'Dispatching'
        },
        {
            id: 3,
            type: 'Route Deviation',
            location: 'Broadway & W 34th St',
            time: '12 mins ago',
            details: 'User vehicle deviated from safe corridor by 500m. No response to check-in notification.',
            priority: 'Medium',
            status: 'Monitoring'
        },
    ]);

    const [recentLogs, setRecentLogs] = useState([
        { id: 101, type: 'SOS Alert', location: 'Broadway St', time: '10:42 AM', details: 'User reported feeling unsafe. Patrol unit #42 responded.', status: 'Resolved' },
        { id: 102, type: 'Geofence Breach', location: 'Times Square', time: '09:15 AM', details: 'Child safety watch exited safe zone. Parent notified.', status: 'Resolved' },
        { id: 103, type: 'SOS Alert', location: 'Brooklyn Bridge', time: 'Yesterday', details: 'Accidental trigger confirmed by user call.', status: 'False Alarm' },
    ]);

    const [stats, setStats] = useState({
        activeUnits: 12,
        totalIncidents: 45,
        avgResponse: '4m 30s'
    });

    return (
        <div className="min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-indigo-100">

            {/* Sidebar / Navigation */}
            <nav className="fixed left-0 top-0 h-full w-20 bg-white/80 backdrop-blur-xl border-r border-indigo-100 flex flex-col items-center py-8 z-50">
                <div className="mb-8 p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl text-white shadow-lg shadow-indigo-200">
                    <Shield size={28} />
                </div>
                <div className="space-y-6 flex flex-col items-center w-full">
                    <NavItem icon={<Radio size={24} />} active color="text-indigo-600" bg="bg-indigo-50" />
                    <NavItem icon={<MapPin size={24} />} />
                    <NavItem icon={<Users size={24} />} />
                    <NavItem icon={<Activity size={24} />} />
                </div>
                <div className="mt-auto pb-8">
                    <img src="https://ui-avatars.com/api/?name=Officer&background=0D8ABC&color=fff" alt="User" className="w-10 h-10 rounded-full border-2 border-white shadow-md shadow-slate-200" />
                </div>
            </nav>

            {/* Main Content */}
            <main className="pl-28 pr-8 py-8 max-w-[1600px] mx-auto">

                {/* Header */}
                <header className="mb-10 flex justify-between items-end">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold uppercase tracking-wider">Officer Dashboard</span>
                        </div>
                        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">Command Center</h1>
                        <p className="text-slate-500 mt-2 text-lg">Real-time monitoring and dispatch interface</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="px-5 py-2.5 bg-white rounded-full border border-emerald-100 shadow-sm flex items-center gap-3 text-sm font-semibold text-emerald-700">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                            </span>
                            System Operational
                        </div>
                        <button className="p-3 bg-white rounded-full border border-slate-200 shadow-sm text-slate-600 hover:bg-slate-50 hover:text-indigo-600 transition-all relative group">
                            <Bell size={22} />
                            <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 border-2 border-white rounded-full"></span>
                            <span className="absolute -bottom-10 right-0 w-max px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity">Notifications</span>
                        </button>
                    </div>
                </header>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                    <StatCard
                        title="Active Patrol Units"
                        value={stats.activeUnits}
                        icon={<Users className="text-white" size={24} />}
                        gradient="bg-gradient-to-br from-blue-500 to-blue-600"
                        shadow="shadow-blue-200"
                        trend="+2 deployed"
                    />
                    <StatCard
                        title="Total Incidents Today"
                        value={stats.totalIncidents}
                        icon={<AlertTriangle className="text-white" size={24} />}
                        gradient="bg-gradient-to-br from-orange-400 to-pink-500"
                        shadow="shadow-orange-200"
                        trend="High volume alert"
                    />
                    <StatCard
                        title="Avg Response Time"
                        value={stats.avgResponse}
                        icon={<Clock className="text-white" size={24} />}
                        gradient="bg-gradient-to-br from-emerald-400 to-teal-500"
                        shadow="shadow-emerald-200"
                        trend="30s faster than avg"
                    />
                </div>

                {/* Dashboard Content Grid */}
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

                    {/* Main Feed / Map Area */}
                    <div className="xl:col-span-2 space-y-8">

                        {/* Live Map Placeholder */}
                        <section className="bg-white p-1.5 rounded-[2rem] shadow-lg shadow-slate-200/50 border border-slate-100 h-96 relative overflow-hidden group">
                            <div className="absolute inset-0 bg-slate-50 rounded-[1.7rem] flex items-center justify-center overflow-hidden">
                                {/* Abstract Map Pattern */}
                                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:16px_16px]"></div>

                                <div className="text-center z-10 glass-card p-8 rounded-3xl">
                                    <MapPin className="mx-auto h-16 w-16 text-indigo-400 mb-4 animate-bounce" />
                                    <p className="text-indigo-900 font-bold text-lg">Live City Map Visualization</p>
                                    <p className="text-slate-500 mt-2">Connecting to GIS Satellite Feed...</p>
                                </div>
                            </div>

                            {/* Map Controls */}
                            <div className="absolute top-6 left-6 flex gap-3">
                                <div className="px-4 py-2 bg-white/90 backdrop-blur-md rounded-xl text-sm font-bold shadow-sm text-slate-700 border border-slate-200 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                                    Manhattan Sector
                                </div>
                            </div>
                            <div className="absolute bottom-6 right-6 flex flex-col gap-2">
                                <div className="w-10 h-10 bg-white hover:bg-indigo-50 hover:text-indigo-600 rounded-xl flex items-center justify-center shadow-md border border-slate-100 cursor-pointer transition-colors">+</div>
                                <div className="w-10 h-10 bg-white hover:bg-indigo-50 hover:text-indigo-600 rounded-xl flex items-center justify-center shadow-md border border-slate-100 cursor-pointer transition-colors">-</div>
                            </div>
                        </section>

                        {/* Active Alerts List */}
                        <section>
                            <h2 className="text-xl font-bold text-slate-900 mb-5 flex items-center gap-3">
                                <div className="p-2 bg-red-100 rounded-lg text-red-600">
                                    <Siren size={24} className="animate-pulse" />
                                </div>
                                Live Critical Alerts
                                <span className="px-2.5 py-0.5 bg-red-100 text-red-600 text-xs rounded-full font-bold ml-auto">
                                    {activeAlerts.length} Active
                                </span>
                            </h2>
                            <div className="space-y-5">
                                {activeAlerts.map((alert) => (
                                    <motion.div
                                        key={alert.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        whileHover={{ scale: 1.01 }}
                                        className={`bg-white p-6 rounded-2xl border-l-4 shadow-sm flex flex-col md:flex-row items-start gap-5 relative overflow-hidden group
                      ${alert.priority === 'Critical' ? 'border-l-purple-600 shadow-purple-100' :
                                                alert.priority === 'High' ? 'border-l-red-500 shadow-red-100' : 'border-l-orange-400 shadow-orange-100'}
                    `}
                                    >
                                        {/* Status Badge */}
                                        <div className="md:hidden mb-2">
                                            <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide
                         ${alert.priority === 'Critical' ? 'bg-purple-100 text-purple-700' :
                                                    alert.priority === 'High' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}
                       `}>
                                                {alert.priority} Priority
                                            </span>
                                        </div>

                                        <div className={`p-4 rounded-2xl shrink-0 ${alert.priority === 'Critical' ? 'bg-purple-50 text-purple-600' :
                                                alert.priority === 'High' ? 'bg-red-50 text-red-500' : 'bg-orange-50 text-orange-500'
                                            }`}>
                                            {alert.type.includes('Voice') ? <Radio size={28} /> :
                                                alert.type.includes('Route') ? <MapPin size={28} /> : <Siren size={28} />}
                                        </div>

                                        <div className="flex-1 w-full">
                                            <div className="flex justify-between items-start mb-1">
                                                <h3 className="text-lg font-bold text-slate-800">{alert.type}</h3>
                                                <span className={`hidden md:inline-block text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide
                           ${alert.priority === 'Critical' ? 'bg-purple-100 text-purple-700' :
                                                        alert.priority === 'High' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}
                        `}>
                                                    {alert.priority} Priority
                                                </span>
                                            </div>

                                            {/* Detailed Description Highlight */}
                                            <div className="mt-2 mb-3 px-4 py-3 bg-slate-50 rounded-xl border border-slate-100 text-slate-700 text-sm font-medium leading-relaxed">
                                                <span className="font-bold text-slate-900 block mb-1 text-xs uppercase tracking-wide opacity-70">Incident Details:</span>
                                                "{alert.details}"
                                            </div>

                                            <div className="flex flex-wrap items-center gap-4 text-xs font-semibold text-slate-500">
                                                <span className="flex items-center gap-1.5 bg-slate-100 px-2.5 py-1 rounded-md">
                                                    <MapPin size={14} className="text-slate-400" /> {alert.location}
                                                </span>
                                                <span className="flex items-center gap-1.5 bg-slate-100 px-2.5 py-1 rounded-md">
                                                    <Clock size={14} className="text-slate-400" /> {alert.time}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="self-center md:self-start flex flex-col gap-2 w-full md:w-auto mt-4 md:mt-0">
                                            <button className={`px-6 py-2.5 text-white text-sm font-bold rounded-xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2
                          ${alert.priority === 'Critical' ? 'bg-purple-600 hover:bg-purple-700 shadow-purple-200' :
                                                    alert.priority === 'High' ? 'bg-red-600 hover:bg-red-700 shadow-red-200' : 'bg-orange-500 hover:bg-orange-600 shadow-orange-200'}
                       `}>
                                                <Radio size={16} /> Dispatch Unit
                                            </button>
                                            <button className="px-6 py-2.5 bg-white border border-slate-200 text-slate-600 text-sm font-bold rounded-xl hover:bg-slate-50 hover:text-slate-900 transition-colors flex items-center justify-center gap-2">
                                                <Phone size={16} /> Contact User
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </section>
                    </div>

                    {/* Right Sidebar: Recent History & Actions */}
                    <div className="space-y-8">

                        {/* Quick Actions */}
                        <section className="grid grid-cols-2 gap-4">
                            <QuickActionCard label="Broadcast Alert" icon={<Radio size={20} />} color="bg-indigo-600" />
                            <QuickActionCard label="Unit Map" icon={<MapPin size={20} />} color="bg-slate-800" />
                            <QuickActionCard label="Generate Report" icon={<Activity size={20} />} color="bg-blue-600" />
                            <QuickActionCard label="Settings" icon={<Shield size={20} />} color="bg-slate-500" />
                        </section>

                        {/* Recent Activity */}
                        <section className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-lg shadow-slate-100">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-lg font-bold text-slate-800">Recent Logs</h2>
                                <button className="text-sm font-semibold text-indigo-600 hover:text-indigo-700">View All</button>
                            </div>

                            <div className="space-y-6 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
                                {recentLogs.map((log) => (
                                    <div key={log.id} className="relative pl-10 group">
                                        <div className={`absolute left-3 top-1.5 w-3 h-3 rounded-full border-2 border-white shadow-sm z-10 
                          ${log.status === 'Resolved' ? 'bg-emerald-500' : 'bg-slate-400'}
                       `}></div>

                                        <div className="flex justify-between items-start mb-1">
                                            <span className="text-sm font-bold text-slate-800">{log.type}</span>
                                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${log.status === 'Resolved' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'
                                                }`}>
                                                {log.status}
                                            </span>
                                        </div>

                                        <p className="text-xs text-slate-500 font-medium mb-2 bg-slate-50 p-2 rounded-lg border border-slate-100">
                                            {log.details}
                                        </p>

                                        <div className="flex justify-between items-center text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                                            <span>{log.location}</span>
                                            <span>{log.time}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>

                </div>
            </main>
        </div>
    );
}

function StatCard({ title, value, icon, trend, gradient, shadow }) {
    return (
        <div className={`relative overflow-hidden p-6 rounded-3xl shadow-xl transition-all hover:-translate-y-1 ${gradient} ${shadow}`}>
            <div className="relative z-10 flex justify-between items-start mb-6">
                <div>
                    <p className="text-white/80 text-sm font-bold tracking-wide mb-1">{title}</p>
                    <h3 className="text-4xl font-black text-white">{value}</h3>
                </div>
                <div className="p-3 bg-white/20 backdrop-blur-md rounded-2xl border border-white/10">
                    {icon}
                </div>
            </div>
            <div className="relative z-10">
                <span className="text-xs font-bold text-white/90 px-2.5 py-1 bg-black/20 rounded-lg inline-block backdrop-blur-sm">
                    {trend}
                </span>
            </div>

            {/* Decorative background shapes */}
            <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
            <div className="absolute top-0 right-1/2 w-24 h-24 bg-white/5 rounded-full blur-xl"></div>
        </div>
    );
}

function QuickActionCard({ label, icon, color }) {
    return (
        <button className={`${color} text-white p-4 rounded-2xl shadow-md hover:shadow-xl hover:scale-[1.02] transition-all flex flex-col items-center gap-3 group`}>
            <div className="p-2 bg-white/20 rounded-xl group-hover:bg-white/30 transition-colors">
                {icon}
            </div>
            <span className="text-xs font-bold text-center">{label}</span>
        </button>
    );
}

function NavItem({ icon, active, color, bg }) {
    return (
        <button className={`p-4 rounded-2xl transition-all duration-300 relative group ${active
                ? `${bg} ${color} shadow-lg shadow-indigo-100`
                : 'text-slate-400 hover:bg-slate-50 hover:text-slate-600'
            }`}>
            {icon}
            {active && <span className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-indigo-600 rounded-l-full"></span>}
        </button>
    );
}
