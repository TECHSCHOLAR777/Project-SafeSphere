'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Heart,
    MapPin,
    Phone,
    Battery,
    Wifi,
    Clock,
    AlertCircle,
    ChevronRight,
    Shield,
    MessageCircle,
    Video
} from 'lucide-react';

export default function GuardianDashboard() {
    const [lovedOne, setLovedOne] = useState({
        name: "Sarah Parker",
        status: "Safe at Work",
        location: "Design District, 4th Ave",
        lastUpdate: "Just now",
        battery: 85,
        signal: "Strong",
        isSafe: true
    });

    const [timeline, setTimeline] = useState([
        { id: 1, time: "09:30 AM", event: "Arrived at Office", type: "safe", icon: <MapPin size={16} /> },
        { id: 2, time: "08:45 AM", event: "Boarded Metro", type: "transit", icon: <Clock size={16} /> },
        { id: 3, time: "08:30 AM", event: "Left Home", type: "transit", icon: <Clock size={16} /> },
    ]);

    const [alerts, setAlerts] = useState([
        { id: 1, type: "Route Deviation", time: "Yesterday, 6:45 PM", message: "Took a different route home (Detour detected).", resolved: true }
    ]);

    return (
        <div className="min-h-screen bg-pink-50/50 text-slate-800 font-sans selection:bg-purple-200">

            {/* Navigation Bar */}
            <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-pink-100 z-50 px-6 py-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-tr from-purple-400 to-pink-400 rounded-xl text-white shadow-lg shadow-pink-200">
                        <Heart size={24} fill="currentColor" />
                    </div>
                    <span className="font-bold text-xl text-purple-900 tracking-tight">Guardian<span className="text-pink-500">View</span></span>
                </div>
                <div className="flex items-center gap-4">
                    <button className="p-2 text-purple-400 hover:text-purple-600 transition-colors">
                        <Shield size={24} />
                    </button>
                    <div className="w-10 h-10 rounded-full bg-purple-100 border-2 border-white shadow-sm overflow-hidden">
                        <img src="https://ui-avatars.com/api/?name=Parent&background=E9D5FF&color=6B21A8" alt="Guardian" />
                    </div>
                </div>
            </nav>

            <main className="pt-24 pb-12 px-4 max-w-6xl mx-auto">

                {/* Header Greeting */}
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-purple-900">
                        Hello, <span className="text-pink-500">Martha</span>
                    </h1>
                    <p className="text-slate-500 mt-1">Here is Sarah's activity for today.</p>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Left Column: Profile & Status */}
                    <div className="space-y-6">

                        {/* Loved One Profile Card */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white rounded-3xl p-6 shadow-xl shadow-purple-100/50 border border-purple-50 relative overflow-hidden"
                        >
                            {/* Decorative Background */}
                            <div className="absolute top-0 right-0 w-32 h-32 bg-pink-100 rounded-full -mr-10 -mt-10 blur-3xl opacity-50"></div>

                            <div className="relative z-10 flex flex-col items-center text-center">
                                <div className="w-24 h-24 rounded-full p-1 bg-gradient-to-br from-purple-300 to-pink-300 mb-4 shadow-lg">
                                    <img
                                        src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=200&h=200"
                                        alt="Sarah"
                                        className="w-full h-full rounded-full object-cover border-4 border-white"
                                    />
                                </div>
                                <h2 className="text-xl font-bold text-slate-800">{lovedOne.name}</h2>
                                <div className="mt-2 px-4 py-1.5 bg-green-50 text-green-600 rounded-full text-sm font-semibold flex items-center gap-1.5 border border-green-100">
                                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                    {lovedOne.status}
                                </div>

                                {/* Vitals */}
                                <div className="flex justify-center gap-6 mt-6 w-full">
                                    <div className="flex flex-col items-center gap-1 text-slate-500">
                                        <Battery size={20} className={lovedOne.battery < 20 ? "text-red-500" : "text-green-500"} />
                                        <span className="text-xs font-semibold">{lovedOne.battery}%</span>
                                    </div>
                                    <div className="w-px h-8 bg-slate-100"></div>
                                    <div className="flex flex-col items-center gap-1 text-slate-500">
                                        <Wifi size={20} className="text-purple-500" />
                                        <span className="text-xs font-semibold">{lovedOne.signal}</span>
                                    </div>
                                    <div className="w-px h-8 bg-slate-100"></div>
                                    <div className="flex flex-col items-center gap-1 text-slate-500">
                                        <Clock size={20} className="text-pink-400" />
                                        <span className="text-xs font-semibold">{lovedOne.lastUpdate}</span>
                                    </div>
                                </div>

                                {/* Quick Actions */}
                                <div className="grid grid-cols-2 gap-3 w-full mt-8">
                                    <button className="py-3 px-4 rounded-xl bg-purple-50 text-purple-700 font-semibold text-sm hover:bg-purple-100 transition-colors flex items-center justify-center gap-2">
                                        <MessageCircle size={18} /> Message
                                    </button>
                                    <button className="py-3 px-4 rounded-xl bg-pink-50 text-pink-600 font-semibold text-sm hover:bg-pink-100 transition-colors flex items-center justify-center gap-2">
                                        <Phone size={18} /> Call
                                    </button>
                                    <button className="col-span-2 py-3 px-4 rounded-xl bg-slate-50 text-slate-600 font-semibold text-sm hover:bg-slate-100 transition-colors flex items-center justify-center gap-2 border border-slate-100">
                                        <Video size={18} /> Live Video Check-in
                                    </button>
                                </div>
                            </div>
                        </motion.div>

                        {/* Previous Alerts */}
                        <div className="bg-white/80 rounded-3xl p-6 border border-white shadow-sm">
                            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                                <AlertCircle size={20} className="text-orange-400" />
                                Alert History
                            </h3>
                            <div className="space-y-4">
                                {alerts.map(alert => (
                                    <div key={alert.id} className="p-4 rounded-2xl bg-orange-50/50 border border-orange-100">
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="font-semibold text-orange-800 text-sm">{alert.type}</span>
                                            <span className="text-xs text-orange-400">{alert.time}</span>
                                        </div>
                                        <p className="text-xs text-orange-700/80 leading-relaxed">{alert.message}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                    </div>

                    {/* Center & Right: Map & Timeline */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* Live Map Card */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-white rounded-[2rem] p-2 shadow-xl shadow-purple-100/30 border border-purple-50 h-[400px] relative group"
                        >
                            <div className="absolute inset-2 bg-slate-100 rounded-[1.7rem] overflow-hidden flex items-center justify-center">
                                {/* Mock Map Background - Using a reliable placeholder if actual map isn't available */}
                                <div className="absolute inset-0 opacity-20 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

                                {/* Location Pin Animation */}
                                <div className="relative z-10 flex flex-col items-center">
                                    <div className="relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pink-400 opacity-75"></span>
                                        <div className="w-16 h-16 bg-white rounded-full shadow-lg p-1 flex items-center justify-center relative">
                                            <img
                                                src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=100&h=100"
                                                alt="Sarah Location"
                                                className="w-full h-full rounded-full object-cover"
                                            />
                                            <div className="absolute -bottom-2 bg-purple-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-md">
                                                Live
                                            </div>
                                        </div>
                                    </div>
                                    <div className="mt-4 bg-white/90 backdrop-blur-md px-4 py-2 rounded-xl shadow-sm border border-slate-100 text-center">
                                        <p className="text-sm font-bold text-slate-800">{lovedOne.location}</p>
                                        <p className="text-xs text-slate-500">Updated now • Accuracy 5m</p>
                                    </div>
                                </div>
                            </div>

                            {/* Map Controls */}
                            <div className="absolute bottom-6 right-6 flex gap-2">
                                <button className="bg-white p-3 rounded-xl shadow-lg shadow-purple-100 text-purple-600 hover:bg-purple-50 transition-colors">
                                    <MapPin size={20} />
                                </button>
                            </div>
                        </motion.div>

                        {/* Activity Timeline */}
                        <div className="bg-white rounded-[2rem] p-8 shadow-sm border border-slate-100">
                            <h3 className="font-bold text-slate-800 text-lg mb-6">Today's Journey</h3>
                            <div className="relative pl-4 space-y-8 before:absolute before:left-[27px] before:top-2 before:bottom-4 before:w-0.5 before:bg-gradient-to-b before:from-purple-200 before:to-transparent">
                                {timeline.map((item, index) => (
                                    <motion.div
                                        key={item.id}
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        className="relative flex items-start gap-4"
                                    >
                                        <div className={`
                         w-6 h-6 rounded-full border-2 border-white shadow-md z-10 flex items-center justify-center shrink-0
                         ${index === 0 ? 'bg-purple-500 text-white ring-4 ring-purple-100' : 'bg-pink-100 text-pink-400'}
                       `}>
                                            {index === 0 ? <div className="w-2 h-2 bg-white rounded-full" /> : item.icon}
                                        </div>
                                        <div className="flex-1 pt-0.5">
                                            <div className="flex justify-between items-start">
                                                <h4 className={`font-semibold ${index === 0 ? 'text-purple-900' : 'text-slate-600'}`}>
                                                    {item.event}
                                                </h4>
                                                <span className="text-xs font-medium text-slate-400 bg-slate-50 px-2 py-1 rounded-full">
                                                    {item.time}
                                                </span>
                                            </div>
                                            {index === 0 && (
                                                <p className="text-sm text-purple-600/80 mt-1">
                                                    Running on schedule. No anomalies detected.
                                                </p>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            <button className="w-full mt-8 py-3 rounded-xl border-2 border-dashed border-slate-200 text-slate-400 font-medium hover:border-purple-200 hover:text-purple-500 transition-colors flex items-center justify-center gap-2">
                                <ChevronRight size={16} /> View Full History
                            </button>
                        </div>

                    </div>
                </div>
            </main>
        </div>
    );
}
