'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield,
    MapPin,
    Navigation,
    AlertTriangle,
    Phone,
    Users,
    Bell,
    Volume2,
    Mic,
    Home,
    Menu,
    X
} from 'lucide-react';

export default function UserDashboard() {
    const [sosActive, setSosActive] = useState(false);
    const [threatDetected, setThreatDetected] = useState(false);
    const [safeRouteActive, setSafeRouteActive] = useState(false);
    const [showMenu, setShowMenu] = useState(false);

    // Simulate threat detection for demo
    useEffect(() => {
        const timer = setTimeout(() => {
            setThreatDetected(true);
        }, 5000);
        return () => clearTimeout(timer);
    }, []);

    return (
        <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-indigo-50 text-slate-800 font-sans selection:bg-pink-200 overflow-hidden relative">

            {/* Background Ambience */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-pink-200/30 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-200/30 rounded-full blur-[100px]"></div>
            </div>

            {/* Header */}
            <nav className="fixed top-0 w-full z-50 px-6 py-4 flex justify-between items-center backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 bg-white/80 rounded-full shadow-sm flex items-center justify-center text-pink-500">
                        <Shield size={20} fill="currentColor" className="opacity-20 translate-y-[1px]" />
                        <Shield size={20} className="absolute" />
                    </div>
                    <span className="font-bold text-lg text-purple-900">SafeSphere</span>
                </div>
                <button onClick={() => setShowMenu(!showMenu)} className="p-2 bg-white/50 hover:bg-white rounded-full transition-colors">
                    <Menu size={24} className="text-purple-900" />
                </button>
            </nav>

            {/* Main Content */}
            <main className="relative z-10 pt-24 pb-32 px-4 max-w-md mx-auto flex flex-col min-h-screen">

                {/* Greeting */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-purple-900 mb-1">Hi, <span className="text-pink-500">Jessica</span></h1>
                    <p className="text-slate-500">You are in a <span className="text-green-600 font-semibold bg-green-50 px-2 py-0.5 rounded-full text-xs border border-green-100">Safe Zone</span></p>
                </div>

                {/* Threat Alert Banner (Conditional) */}
                <AnimatePresence>
                    {threatDetected && (
                        <motion.div
                            initial={{ opacity: 0, y: -20, height: 0 }}
                            animate={{ opacity: 1, y: 0, height: 'auto' }}
                            exit={{ opacity: 0, y: -20, height: 0 }}
                            className="mb-8"
                        >
                            <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 shadow-xl shadow-red-100 border border-red-50 flex items-start gap-4 ring-2 ring-red-100 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
                                <div className="p-2 bg-red-100 text-red-500 rounded-full shrink-0 animate-pulse">
                                    <AlertTriangle size={24} />
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-bold text-red-600">Threat Detected Nearby</h3>
                                    <p className="text-xs text-slate-600 mt-1">Loud noise detected 200m ahead. Recommending alternative route.</p>
                                    <div className="flex gap-2 mt-3">
                                        <button className="px-3 py-1.5 bg-red-500 text-white text-xs font-bold rounded-lg shadow-md shadow-red-200">Avoid Area</button>
                                        <button onClick={() => setThreatDetected(false)} className="px-3 py-1.5 bg-slate-100 text-slate-500 text-xs font-bold rounded-lg">Dismiss</button>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Main SOS Button */}
                <div className="flex-1 flex flex-col items-center justify-center mb-10 relative">

                    {/* Ripple Effects behind SOS */}
                    {sosActive && (
                        <>
                            <div className="absolute w-64 h-64 bg-red-500/10 rounded-full animate-ping"></div>
                            <div className="absolute w-80 h-80 bg-red-500/5 rounded-full animate-ping [animation-delay:0.2s]"></div>
                        </>
                    )}

                    <button
                        onClick={() => setSosActive(!sosActive)}
                        className={`w-48 h-48 rounded-full shadow-2xl flex flex-col items-center justify-center transition-all duration-300 transform active:scale-95 relative z-20 group
               ${sosActive
                                ? 'bg-red-500 shadow-red-500/40 translate-y-2'
                                : 'bg-white shadow-purple-200 hover:shadow-purple-300'
                            }
             `}
                    >
                        {sosActive ? (
                            <>
                                <span className="text-white font-black text-4xl tracking-widest animate-pulse">SOS</span>
                                <span className="text-white/80 text-xs mt-1 font-semibold">SENDING ALERT...</span>
                            </>
                        ) : (
                            <div className="bg-gradient-to-br from-pink-500 to-purple-600 text-transparent bg-clip-text flex flex-col items-center">
                                <span className="font-black text-4xl tracking-widest drop-shadow-sm">SOS</span>
                                <span className="text-slate-400 text-[10px] mt-1 font-semibold tracking-wider">HOLD 3 SEC</span>
                            </div>
                        )}

                        {/* Decorative Ring */}
                        {!sosActive && (
                            <div className="absolute inset-2 border-2 border-dashed border-purple-100 rounded-full group-hover:border-purple-200 transition-colors"></div>
                        )}
                    </button>

                    <p className="mt-6 text-sm font-medium text-slate-400">
                        {sosActive ? "Notifying Emergency Contacts & Police..." : "Tap for Emergency Assistance"}
                    </p>
                </div>

                {/* Feature Cards Grid */}
                <div className="grid grid-cols-2 gap-4">

                    {/* Safe Route */}
                    <motion.div
                        whileTap={{ scale: 0.98 }}
                        className="bg-white/60 backdrop-blur-sm p-4 rounded-3xl border border-white shadow-sm flex flex-col items-center text-center gap-2 cursor-pointer hover:bg-white/80 transition-colors"
                    >
                        <div className="p-3 bg-blue-50 text-blue-500 rounded-2xl mb-1">
                            <Navigation size={24} />
                        </div>
                        <h3 className="font-bold text-slate-700 text-sm">Safe Route</h3>
                        <p className="text-[10px] text-slate-400 leading-tight">AI-powered safest path to destination</p>
                    </motion.div>

                    {/* Fake Call */}
                    <motion.div
                        whileTap={{ scale: 0.98 }}
                        className="bg-white/60 backdrop-blur-sm p-4 rounded-3xl border border-white shadow-sm flex flex-col items-center text-center gap-2 cursor-pointer hover:bg-white/80 transition-colors"
                    >
                        <div className="p-3 bg-purple-50 text-purple-500 rounded-2xl mb-1">
                            <Phone size={24} />
                        </div>
                        <h3 className="font-bold text-slate-700 text-sm">Fake Call</h3>
                        <p className="text-[10px] text-slate-400 leading-tight">Simulate an incoming call instantly</p>
                    </motion.div>

                    {/* Threat Map */}
                    <div className="col-span-2 bg-white/60 backdrop-blur-md p-5 rounded-3xl border border-white shadow-sm hover:shadow-md transition-shadow cursor-pointer relative overflow-hidden group">
                        <div className="relative z-10 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 bg-orange-50 text-orange-500 rounded-xl">
                                    <MapPin size={22} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-slate-700">Threat Map</h3>
                                    <p className="text-xs text-slate-500">2 reports near your location</p>
                                </div>
                            </div>
                            <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm text-slate-400">
                                <AlertTriangle size={14} />
                            </div>
                        </div>

                        {/* Decorative Map Pattern */}
                        <div className="absolute inset-0 opacity-5 bg-[radial-gradient(#64748b_1px,transparent_1px)] [background-size:8px_8px] group-hover:opacity-10 transition-opacity"></div>
                        <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-orange-100/50 rounded-full blur-2xl"></div>
                    </div>

                </div>

            </main>

            {/* Bottom Navigation Bar */}
            <div className="fixed bottom-6 left-6 right-6 h-16 bg-white/90 backdrop-blur-xl rounded-full shadow-2xl shadow-purple-900/10 border border-white/50 flex items-center justify-around px-2 z-50">
                <NavIcon icon={<Home size={22} />} active />
                <NavIcon icon={<MapPin size={22} />} />
                <div className="w-12"></div> {/* Spacing for SOS button visual flow if needed, or just centering */}
                <NavIcon icon={<Users size={22} />} />
                <NavIcon icon={<Mic size={22} />} />
            </div>

        </div>
    );
}

function NavIcon({ icon, active }) {
    return (
        <button className={`p-3 rounded-full transition-all ${active ? 'text-pink-500 bg-pink-50' : 'text-slate-400 hover:text-slate-600'
            }`}>
            {icon}
        </button>
    )
}
