/* ============================================
   SAFESPHERE - VANILLA JAVASCRIPT
   ============================================ */

// ============================================
// TOAST NOTIFICATIONS
// ============================================
import supabase from './Supabase.js';
class Toast {
    static show(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 300ms ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Add slideOutRight animation dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============================================
// CHAT WIDGET - COMPLETE REWRITE
// ============================================

class ChatWidget {
    constructor() {
        // Get all DOM elements
        this.widget = document.querySelector('.chat-widget');
        this.trigger = document.getElementById('chatTrigger');
        this.container = document.getElementById('chatContainer');
        this.closeBtn = document.getElementById('chatClose');
        this.messagesContainer = document.getElementById('chatMessages');
        this.inputField = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('chatSend');
        this.isOpen = false;

        // Verify all elements exist
        if (!this.trigger || !this.container || !this.closeBtn || !this.messagesContainer) {
            console.error('❌ Chat Widget: Missing required elements');
            console.log('Elements:', {
                trigger: !!this.trigger,
                container: !!this.container,
                closeBtn: !!this.closeBtn,
                messagesContainer: !!this.messagesContainer
            });
            return;
        }

        // Initialize event listeners
        this.attachEventListeners();
        console.log('✅ Chat Widget: Initialized successfully');
        console.log('Widget container:', this.container);
    }

    attachEventListeners() {
        // Main trigger button
        this.trigger.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleChat();
        });

        // Close button
        this.closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.closeChat();
        });

        // Send button
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSendMessage();
            });
        }

        // Enter key in input
        if (this.inputField) {
            this.inputField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }

        // Quick prompts
        document.querySelectorAll('.quick-prompt').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const prompt = btn.textContent.trim();
                this.sendMessageWithText(prompt);
            });
        });

        // Close chat when clicking outside the widget
        document.addEventListener('click', (e) => {
            // Only close if chat is open and click is outside
            if (this.isOpen && this.widget && !this.widget.contains(e.target)) {
                this.closeChat();
            }
        });
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        this.isOpen = true;
        console.log('Opening chat...');
        console.log('Before: container classes =', this.container.className);
        
        // Only manipulate what's needed
        this.container.classList.add('open');
        this.trigger.classList.add('hidden');
        
        console.log('After: container classes =', this.container.className);
        console.log('Computed style opacity:', window.getComputedStyle(this.container).opacity);
        console.log('Computed style visibility:', window.getComputedStyle(this.container).visibility);
        
        // Delay focus to ensure smooth animation
        setTimeout(() => {
            if (this.inputField) {
                this.inputField.focus();
            }
        }, 300);

        console.log('✅ Chat opened');
    }

    closeChat() {
        this.isOpen = false;
        console.log('Closing chat...');
        
        // Remove open class from container
        this.container.classList.remove('open');
        // Show trigger button again
        this.trigger.classList.remove('hidden');
        
        console.log('✅ Chat closed');
    }

    handleSendMessage() {
        const text = this.inputField ? this.inputField.value.trim() : '';
        if (!text) return;
        
        this.sendMessageWithText(text);
    }

    sendMessageWithText(text) {
        // Add user message
        this.addMessage(text, 'user');
        
        // Clear input
        if (this.inputField) {
            this.inputField.value = '';
        }

        // Simulate bot typing indicator
        this.addMessage('Typing...', 'bot-typing');

        // Generate and send bot response
        setTimeout(() => {
            // Remove typing indicator
            const typingMsg = this.messagesContainer.querySelector('.bot-typing-message');
            if (typingMsg) typingMsg.remove();
            
            // Add bot response
            const response = this.generateBotResponse(text);
            this.addMessage(response, 'bot');
        }, 1200);
    }

    addMessage(text, sender) {
        if (!this.messagesContainer) return;

        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${sender === 'user' ? 'user-msg' : 'bot-msg'}`;

        const messageBubble = document.createElement('div');
        messageBubble.className = `message-bubble ${sender}-message`;
        
        // Handle multi-line text
        const lines = text.split('\n');
        lines.forEach((line, index) => {
            if (line.trim()) {
                const p = document.createElement('p');
                p.textContent = line;
                messageBubble.appendChild(p);
                if (index < lines.length - 1) {
                    messageBubble.appendChild(document.createElement('br'));
                }
            }
        });

        messageWrapper.appendChild(messageBubble);
        this.messagesContainer.appendChild(messageWrapper);
        
        // Auto-scroll to bottom
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 0);
    }

    generateBotResponse(userMessage) {
        const msg = userMessage.toLowerCase();

        // Safety emergency responses
        if (/unsafe|danger|threat|abuse|hit|attack|violence/i.test(msg)) {
            return "🚨 EMERGENCY PROTOCOL ACTIVATED\n\n✓ Sharing location with trusted contacts\n✓ Alerting nearby authorities\n✓ Recording incident\n\nStay safe. Press SOS for immediate help.";
        }

        // Following/stalking
        if (/follow|stalking|stalker|being followed|tail|pursuit/i.test(msg)) {
            return "⚠️ IMMEDIATE ACTION NEEDED\n\n✓ Move to crowded public area\n✓ Call Police: India (100), USA (911), UK (999)\n✓ Alert trusted contacts\n\nDo not confront. Stay visible in public.";
        }

        // Legal help
        if (/legal|law|rights|court|fir|complaint|justice/i.test(msg)) {
            return "⚖️ YOUR LEGAL RIGHTS\n\n1. File FIR (First Information Report)\n2. Protection Order from courts\n3. Restraining order against stalker\n4. Evidence collection is your right\n5. Self-defense is legal\n\nContact: Legal Aid Cell (toll-free)";
        }

        // Emergency services
        if (/emergency|police|ambulance|hospital|911|112/i.test(msg)) {
            return "🚨 EMERGENCY CONTACTS\n\n🇮🇳 India:\n• Police: 100\n• Ambulance: 102\n• Women Helpline: 1091\n\n🇺🇸 USA: 911\n🇬🇧 UK: 999\n🇪🇺 EU: 112";
        }

        // Emotional support
        if (/afraid|scared|fear|anxiety|panic|stress|depressed/i.test(msg)) {
            return "💪 YOUR FEELINGS ARE VALID\n\n✓ You're not alone\n✓ Trust your instincts\n✓ Talk to someone you trust\n✓ Professional help is available\n\nHotlines:\n• AASRA: 9820466726\n• iCall: 9152987821";
        }

        // Self-defense
        if (/defense|self-defense|protect|safety/i.test(msg)) {
            return "🛡️ SAFETY & SELF-DEFENSE\n\n✓ Take self-defense classes\n✓ Carry whistle/keychain\n✓ Trust your gut feeling\n✓ Stay alert, aware\n✓ Plan escape routes\n\nOur app features:\n• Safe route planning\n• Nearby help finder\n• Live location sharing";
        }

        // Help/support general
        if (/help|assist|support|guide|advice/i.test(msg)) {
            return "🤝 HOW CAN I HELP?\n\n📍 Route Safety\n🗺️ Find Nearby Help\n🆘 Emergency Contacts\n⚖️ Legal Information\n🛡️ Self-Defense Tips\n💪 Emotional Support\n📚 Educational Resources\n\nWhat do you need?";
        }

        // Mental health
        if (/mental|health|counseling|therapy|depression/i.test(msg)) {
            return "🧠 MENTAL HEALTH SUPPORT\n\n✓ Therapy & counseling\n✓ Support groups\n✓ Meditation resources\n✓ Hotlines & chat support\n\nFree Resources:\n• MyIndianFamily.com\n• Psychology Today (therapist finder)";
        }

        // Default response
        return "👋 I'm Sakhi, your safety AI assistant.\n\nI can help with:\n🆘 Emergencies\n⚖️ Legal Rights\n📍 Safe Routes\n🛡️ Self-Defense\n💪 Emotional Support\n\nWhat's on your mind?";
    }
}

// ============================================
// ACTION CARDS & SOS BUTTON
// ============================================

class ActionHandler {
    static init() {
        // Action cards
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.addEventListener('click', () => {
                const action = card.dataset.action;
                ActionHandler.handleAction(action);
            });
        });

        // SOS Button
        const sosButton = document.getElementById('sosButton');
        sosButton.addEventListener('click', () => ActionHandler.triggerSOS());
    }

    static handleAction(action) {
        const messages = {
            call: '☎️ Calling Emergency Services (911)...',
            location: '📍 Location Shared with emergency contacts!',
            voice: '🎤 Voice SOS Recording Started...',
            'fake-call': '☎️ Fake Call Initiated...'
        };

        Toast.show(messages[action] || 'Action triggered', 'info');
    }

    static triggerSOS() {
        Toast.show('🚨 SOS Alert Sent! Emergency contacts notified.', 'error', 4000);
        
        // Try to send to API
<<<<<<< HEAD
        const API_URL = 'https://improved-train-v679p9p5jr5p35gp-8000.app.github.dev/api/sos';
=======
        const API_URL = 'https://stunning-halibut-974rgpw767pp3pxgg-8000.app.github.dev/api/sos';
>>>>>>> 3c57bd1 (use page initiated)

        const sendSOS = (latitude = 0, longitude = 0) => {
            fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'SOS',
                    details: 'SOS Button Pressed',
                    location: { lat: latitude, lng: longitude }
                })
            }).catch((error) => {
                // Offline mode
                console.error("SOS API Failed:", error);
                console.log('API unavailable - running in offline mode');
            });
        };

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => sendSOS(position.coords.latitude, position.coords.longitude),
                (error) => {
                    console.error("Geolocation error:", error);
                    sendSOS();
                }
            );
        } else {
            sendSOS();
        }

        // Visual feedback
        const sosButton = document.getElementById('sosButton');
        sosButton.style.animation = 'none';
        setTimeout(() => {
            sosButton.style.animation = '';
        }, 100);
    }
}

// ============================================
// SMOOTH SCROLLING
// ============================================

class SmoothScroll {
    static init() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
}

// ============================================
// RESPONSIVE MENU
// ============================================

class MenuHandler {
    static init() {
        const menuToggle = document.querySelector('.menu-toggle');
        const navbarLinks = document.querySelector('.navbar-links');

        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                navbarLinks.style.display = navbarLinks.style.display === 'flex' ? 'none' : 'flex';
            });
        }
    }
}

// ============================================
// INITIALIZE ALL
// ============================================

try {
    console.log('⏳ Initializing SafeSphere...');
    
    // Initialize chat widget
    new ChatWidget();
    console.log('✅ Chat widget ready');

    // Initialize action handlers
    ActionHandler.init();
    console.log('✅ Actions ready');

    // Initialize smooth scrolling
    SmoothScroll.init();
    console.log('✅ Navigation ready');

    // Initialize responsive menu
    MenuHandler.init();
    console.log('✅ Menu ready');

    // Ensure an application container exists for role pages
    if (!document.getElementById('app')) {
        const app = document.createElement('div');
        app.id = 'app';
        document.body.appendChild(app);
    }

    // ============================================
    // INLINE DASHBOARD PAGES
    // ============================================

    // USER DASHBOARD
    const UserPage = {
        init(params = {}) {
            const app = document.getElementById('app');
            
            let sosActive = false;
            let threatDetected = false;

            // Show threat after 5 seconds for demo
            setTimeout(() => {
                threatDetected = true;
                updateThreatAlert();
            }, 5000);

            function updateThreatAlert() {
                const threatAlert = app.querySelector('.threat-alert');
                if (threatAlert) {
                    if (threatDetected) {
                        threatAlert.style.display = 'flex';
                        threatAlert.style.animation = 'slideDown 400ms ease-out';
                    } else {
                        threatAlert.style.opacity = '0';
                        setTimeout(() => {
                            threatAlert.style.display = 'none';
                        }, 300);
                    }
                }
            }

            app.innerHTML = `
                <div class="user-dashboard-wrapper">
                    <!-- Background Ambience -->
                    <div class="dashboard-background">
                        <div class="bg-blob bg-blob-1"></div>
                        <div class="bg-blob bg-blob-2"></div>
                    </div>

                    <!-- Main Content -->
                    <main class="user-main-content">
                        <!-- Greeting Section -->
                        <div class="user-greeting">
                            <h1>Hi, <span class="text-highlight">Jessica</span></h1>
                            <p>You are in a <span class="safe-zone-badge">Safe Zone</span></p>
                        </div>

                        <!-- Threat Alert Banner -->
                        <div class="threat-alert" style="display: ${threatDetected ? 'flex' : 'none'}">
                            <div class="threat-alert-bar"></div>
                            <div class="threat-icon">⚠️</div>
                            <div class="threat-content">
                                <h3>Threat Detected Nearby</h3>
                                <p>Loud noise detected 200m ahead. Recommending alternative route.</p>
                                <div class="threat-actions">
                                    <button class="btn-avoid">Avoid Area</button>
                                    <button class="btn-dismiss" id="dismiss-threat">Dismiss</button>
                                </div>
                            </div>
                        </div>

                        <!-- SOS Button Section -->
                        <div class="sos-section">
                            ${sosActive ? '<div class="ripple ripple-1"></div><div class="ripple ripple-2"></div>' : ''}
                            <button class="sos-button ${sosActive ? 'active' : ''}" id="sos-btn">
                                <div class="sos-content">
                                    <span class="sos-text">${sosActive ? 'SOS' : 'SOS'}</span>
                                    <span class="sos-subtext">${sosActive ? 'SENDING ALERT...' : 'HOLD 3 SEC'}</span>
                                </div>
                                ${!sosActive ? '<div class="sos-ring"></div>' : ''}
                            </button>
                            <p class="sos-message">${sosActive ? 'Notifying Emergency Contacts & Police...' : 'Tap for Emergency Assistance'}</p>
                        </div>

                        <!-- Feature Cards -->
                        <div class="feature-cards-grid">
                            <!-- Safe Route Card -->
                            <div class="feature-card feature-card-blue">
                                <div class="feature-icon">🧭</div>
                                <h3>Safe Route</h3>
                                <p>AI-powered safest path to destination</p>
                            </div>

                            <!-- Fake Call Card -->
                            <div class="feature-card feature-card-purple">
                                <div class="feature-icon">☎️</div>
                                <h3>Fake Call</h3>
                                <p>Simulate an incoming call instantly</p>
                            </div>

                            <!-- Threat Map Card -->
                            <div class="feature-card feature-card-wide feature-card-orange">
                                <div class="feature-icon-group">
                                    <div class="feature-icon-large">📍</div>
                                    <div class="feature-info">
                                        <h3>Threat Map</h3>
                                        <p>2 reports near your location</p>
                                    </div>
                                </div>
                                <div class="feature-alert-badge">⚠️</div>
                                <div class="feature-card-pattern"></div>
                            </div>
                        </div>
                    </main>

                    <!-- Bottom Navigation -->
                    <nav class="bottom-nav">
                        <button class="nav-btn nav-btn-active">🏠</button>
                        <button class="nav-btn">📍</button>
                        <button class="nav-btn">👥</button>
                        <button class="nav-btn">🎤</button>
                    </nav>
                </div>
            `;

            // Event listeners
            const sosBtn = app.getElementById('sos-btn');
            sosBtn?.addEventListener('click', () => {
                sosActive = !sosActive;
                sosBtn.innerHTML = `
                    <div class="sos-content">
                        <span class="sos-text">${sosActive ? 'SOS' : 'SOS'}</span>
                        <span class="sos-subtext">${sosActive ? 'SENDING ALERT...' : 'HOLD 3 SEC'}</span>
                    </div>
                    ${!sosActive ? '<div class="sos-ring"></div>' : ''}
                `;
                sosBtn.classList.toggle('active');
                
                const sosMessage = app.querySelector('.sos-message');
                if (sosMessage) {
                    sosMessage.textContent = sosActive ? 'Notifying Emergency Contacts & Police...' : 'Tap for Emergency Assistance';
                }

                if (sosActive) {
                    Toast.show('🚨 SOS Alert Activated! Emergency contacts notified.', 'success');
                } else {
                    Toast.show('🔴 SOS Alert Deactivated', 'info');
                }
            });

            const dismissBtn = app.getElementById('dismiss-threat');
            dismissBtn?.addEventListener('click', () => {
                threatDetected = false;
                updateThreatAlert();
                Toast.show('✓ Threat alert dismissed', 'info');
            });

            const avoidBtn = app.querySelector('.btn-avoid');
            avoidBtn?.addEventListener('click', () => {
                Toast.show('📍 Alternative route calculated', 'info');
            });

            // Feature card clicks
            const featureCards = app.querySelectorAll('.feature-card');
            featureCards.forEach(card => {
                card.addEventListener('click', () => {
                    const title = card.querySelector('h3')?.textContent;
                    Toast.show(`✓ ${title} activated`, 'info');
                });
            });

            // Nav button clicks
            const navBtns = app.querySelectorAll('.nav-btn');
            navBtns.forEach((btn, index) => {
                btn.addEventListener('click', () => {
                    navBtns.forEach(b => b.classList.remove('nav-btn-active'));
                    btn.classList.add('nav-btn-active');
                });
            });
        },

        teardown() {
            const app = document.getElementById('app');
            if (app) app.innerHTML = '';
        }
    };

    // GUARDIAN DASHBOARD
    const GuardianPage = {
        init(params = {}) {
            const app = document.getElementById('app');
            
            // Guardian data
            const lovedOne = {
                name: "Sarah Parker",
                status: "Safe at Work",
                location: "Design District, 4th Ave",
                lastUpdate: "Just now",
                battery: 85,
                signal: "Strong",
                isSafe: true
            };

            const timeline = [
                { id: 1, time: "09:30 AM", event: "Arrived at Office", type: "safe" },
                { id: 2, time: "08:45 AM", event: "Boarded Metro", type: "transit" },
                { id: 3, time: "08:30 AM", event: "Left Home", type: "transit" },
            ];

            const alerts = [
                { id: 1, type: "Route Deviation", time: "Yesterday, 6:45 PM", message: "Took a different route home (Detour detected).", resolved: true }
            ];

            app.innerHTML = `
                <div class="guardian-dashboard-container">
                    <!-- Header Greeting -->
                    <header class="guardian-header">
                        <h1>Hello, <span class="text-pink">Martha</span></h1>
                        <p>Here is Sarah's activity for today.</p>
                    </header>

                    <div class="guardian-grid">
                        <!-- Left Column: Profile & Status -->
                        <div class="guardian-left-column">

                            <!-- Loved One Profile Card -->
                            <div class="profile-card">
                                <div class="profile-avatar">
                                    <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=200&h=200" alt="Sarah" />
                                </div>
                                <h2 class="profile-name">${lovedOne.name}</h2>
                                <div class="profile-status safe">
                                    <span class="status-dot"></span>
                                    ${lovedOne.status}
                                </div>

                                <!-- Vitals -->
                                <div class="vitals-section">
                                    <div class="vital">
                                        <span class="vital-icon">🔋</span>
                                        <span class="vital-value">${lovedOne.battery}%</span>
                                    </div>
                                    <div class="vital-divider"></div>
                                    <div class="vital">
                                        <span class="vital-icon">📶</span>
                                        <span class="vital-value">${lovedOne.signal}</span>
                                    </div>
                                    <div class="vital-divider"></div>
                                    <div class="vital">
                                        <span class="vital-icon">🕐</span>
                                        <span class="vital-value">${lovedOne.lastUpdate}</span>
                                    </div>
                                </div>

                                <!-- Quick Actions -->
                                <div class="quick-actions">
                                    <button class="action-btn message-btn" id="guardian-message">💬 Message</button>
                                    <button class="action-btn call-btn" id="guardian-call">☎️ Call</button>
                                    <button class="action-btn video-btn" id="guardian-video">🎥 Video Check-in</button>
                                </div>
                            </div>

                            <!-- Alert History -->
                            <div class="alert-history">
                                <h3>⚠️ Alert History</h3>
                                <div class="alerts-list">
                                    ${alerts.map(alert => `
                                        <div class="alert-item">
                                            <div class="alert-header">
                                                <span class="alert-type">${alert.type}</span>
                                                <span class="alert-time">${alert.time}</span>
                                            </div>
                                            <p class="alert-message">${alert.message}</p>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>

                        <!-- Right Column: Map & Timeline -->
                        <div class="guardian-right-column">
                            <!-- Live Map Card -->
                            <div class="live-map-card">
                                <div class="map-container">
                                    <div class="map-grid"></div>
                                    <div class="location-pin">
                                        <div class="ping-animation"></div>
                                        <div class="pin-avatar">
                                            <img src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=100&h=100" alt="Sarah" />
                                            <span class="live-badge">Live</span>
                                        </div>
                                        <div class="location-info">
                                            <p class="location-name">${lovedOne.location}</p>
                                            <p class="location-meta">Updated now • Accuracy 5m</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="map-controls">
                                    <button class="map-btn" id="guardian-map">📍</button>
                                </div>
                            </div>

                            <!-- Activity Timeline -->
                            <div class="activity-timeline">
                                <h3>Today's Journey</h3>
                                <div class="timeline-items">
                                    ${timeline.map((item, index) => `
                                        <div class="timeline-item" style="animation-delay: ${index * 100}ms">
                                            <div class="timeline-dot ${index === 0 ? 'active' : ''}"></div>
                                            <div class="timeline-content">
                                                <div class="timeline-header">
                                                    <h4>${item.event}</h4>
                                                    <span class="timeline-time">${item.time}</span>
                                                </div>
                                                ${index === 0 ? '<p class="timeline-status">Running on schedule. No anomalies detected.</p>' : ''}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                                <button class="view-history-btn">→ View Full History</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Attach event listeners
            document.getElementById('guardian-message')?.addEventListener('click', () => {
                Toast.show('💬 Opening message to Sarah...', 'info');
            });

            document.getElementById('guardian-call')?.addEventListener('click', () => {
                Toast.show('☎️ Calling Sarah...', 'info');
            });

            document.getElementById('guardian-video')?.addEventListener('click', () => {
                Toast.show('🎥 Starting video check-in...', 'info');
            });

            document.getElementById('guardian-map')?.addEventListener('click', () => {
                Toast.show('📍 Opening live map...', 'info');
            });
        },

        teardown() {
            const app = document.getElementById('app');
            if (app) app.innerHTML = '';
        }
    };

    // POLICE DASHBOARD
    const PolicePage = {
        init(params = {}) {
            const app = document.getElementById('app');
            
            const activeAlerts = [
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
            ];

            const recentLogs = [
                { id: 101, type: 'SOS Alert', location: 'Broadway St', time: '10:42 AM', details: 'User reported feeling unsafe. Patrol unit #42 responded.', status: 'Resolved' },
                { id: 102, type: 'Geofence Breach', location: 'Times Square', time: '09:15 AM', details: 'Child safety watch exited safe zone. Parent notified.', status: 'Resolved' },
                { id: 103, type: 'SOS Alert', location: 'Brooklyn Bridge', time: 'Yesterday', details: 'Accidental trigger confirmed by user call.', status: 'False Alarm' },
            ];

            const stats = {
                activeUnits: 12,
                totalIncidents: 45,
                avgResponse: '4m 30s'
            };

            app.innerHTML = `
                <div class="police-dashboard-wrapper">
                    <!-- Sidebar Navigation -->
                    <nav class="police-sidebar">
                        <div class="sidebar-logo">🛡️</div>
                        <div class="sidebar-icons">
                            <button class="nav-icon active">📡</button>
                            <button class="nav-icon">📍</button>
                            <button class="nav-icon">👥</button>
                            <button class="nav-icon">📊</button>
                        </div>
                        <div class="sidebar-profile">
                            <img src="https://ui-avatars.com/api/?name=Officer&background=0D8ABC&color=fff" alt="Officer" />
                        </div>
                    </nav>

                    <!-- Main Content -->
                    <main class="police-main">
                        <!-- Header -->
                        <header class="police-header">
                            <div class="header-left">
                                <span class="header-badge">Officer Dashboard</span>
                                <h1>Command Center</h1>
                                <p>Real-time monitoring and dispatch interface</p>
                            </div>
                            <div class="header-right">
                                <div class="status-indicator">
                                    <span class="status-pulse"></span>
                                    System Operational
                                </div>
                                <button class="notification-btn" id="police-notifications">
                                    🔔
                                    <span class="notification-dot"></span>
                                </button>
                            </div>
                        </header>

                        <!-- Stats Grid -->
                        <div class="stats-grid">
                            <div class="stat-card stat-blue">
                                <div class="stat-icon">👥</div>
                                <div class="stat-content">
                                    <p class="stat-label">Active Patrol Units</p>
                                    <h3 class="stat-value">${stats.activeUnits}</h3>
                                    <span class="stat-trend">+2 deployed</span>
                                </div>
                            </div>
                            <div class="stat-card stat-orange">
                                <div class="stat-icon">⚠️</div>
                                <div class="stat-content">
                                    <p class="stat-label">Total Incidents Today</p>
                                    <h3 class="stat-value">${stats.totalIncidents}</h3>
                                    <span class="stat-trend">High volume alert</span>
                                </div>
                            </div>
                            <div class="stat-card stat-green">
                                <div class="stat-icon">⏱️</div>
                                <div class="stat-content">
                                    <p class="stat-label">Avg Response Time</p>
                                    <h3 class="stat-value">${stats.avgResponse}</h3>
                                    <span class="stat-trend">30s faster than avg</span>
                                </div>
                            </div>
                        </div>

                        <!-- Main Content Grid -->
                        <div class="police-content-grid">
                            <!-- Left: Map & Alerts -->
                            <div class="police-main-feed">
                                <!-- Live Map -->
                                <section class="live-map">
                                    <div class="map-container">
                                        <div class="map-grid"></div>
                                        <div class="map-placeholder">
                                            <div class="map-icon">📍</div>
                                            <p class="map-title">Live City Map Visualization</p>
                                            <p class="map-subtitle">Connecting to GIS Satellite Feed...</p>
                                        </div>
                                        <div class="map-header-badge">
                                            <span class="map-dot"></span>
                                            Manhattan Sector
                                        </div>
                                        <div class="map-controls">
                                            <button class="map-btn">+</button>
                                            <button class="map-btn">−</button>
                                        </div>
                                    </div>
                                </section>

                                <!-- Active Alerts -->
                                <section class="alerts-section">
                                    <h2 class="alerts-title">
                                        <span class="alerts-icon">🚨</span>
                                        Live Critical Alerts
                                        <span class="alerts-count">${activeAlerts.length} Active</span>
                                    </h2>
                                    <div class="alerts-list">
                                        ${activeAlerts.map((alert, index) => `
                                            <div class="alert-card alert-${alert.priority.toLowerCase()}" style="animation-delay: ${index * 100}ms">
                                                <div class="alert-icon alert-icon-${alert.priority.toLowerCase()}">
                                                    ${alert.type.includes('Voice') ? '📻' : alert.type.includes('Route') ? '📍' : '🚨'}
                                                </div>
                                                <div class="alert-content">
                                                    <div class="alert-header-line">
                                                        <h3 class="alert-type">${alert.type}</h3>
                                                        <span class="alert-priority alert-priority-${alert.priority.toLowerCase()}">${alert.priority} Priority</span>
                                                    </div>
                                                    <div class="alert-details-box">
                                                        <span class="details-label">Incident Details:</span>
                                                        <p class="details-text">"${alert.details}"</p>
                                                    </div>
                                                    <div class="alert-meta">
                                                        <span class="meta-item">📍 ${alert.location}</span>
                                                        <span class="meta-item">🕐 ${alert.time}</span>
                                                    </div>
                                                </div>
                                                <div class="alert-actions">
                                                    <button class="btn-dispatch alert-btn-${alert.priority.toLowerCase()}">
                                                        📡 Dispatch Unit
                                                    </button>
                                                    <button class="btn-contact">☎️ Contact User</button>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </section>
                            </div>

                            <!-- Right Sidebar -->
                            <aside class="police-sidebar-right">
                                <!-- Quick Actions -->
                                <section class="quick-actions">
                                    <button class="quick-action-btn qa-indigo">📡<span>Broadcast Alert</span></button>
                                    <button class="quick-action-btn qa-slate">📍<span>Unit Map</span></button>
                                    <button class="quick-action-btn qa-blue">📊<span>Generate Report</span></button>
                                    <button class="quick-action-btn qa-gray">⚙️<span>Settings</span></button>
                                </section>

                                <!-- Recent Logs -->
                                <section class="recent-logs">
                                    <div class="logs-header">
                                        <h2>Recent Logs</h2>
                                        <button class="view-all-btn">View All</button>
                                    </div>
                                    <div class="logs-list">
                                        <div class="logs-timeline"></div>
                                        ${recentLogs.map((log) => `
                                            <div class="log-item">
                                                <div class="log-dot log-${log.status.toLowerCase().replace(' ', '-')}"></div>
                                                <div class="log-content">
                                                    <div class="log-header">
                                                        <span class="log-type">${log.type}</span>
                                                        <span class="log-status log-status-${log.status.toLowerCase().replace(' ', '-')}">${log.status}</span>
                                                    </div>
                                                    <p class="log-details">${log.details}</p>
                                                    <div class="log-footer">
                                                        <span class="log-location">${log.location}</span>
                                                        <span class="log-time">${log.time}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </section>
                            </aside>
                        </div>
                    </main>
                </div>
            `;

            // Event listeners
            document.getElementById('police-notifications')?.addEventListener('click', () => {
                Toast.show('🔔 Notification center opened', 'info');
            });

            const dispatchButtons = app.querySelectorAll('.btn-dispatch');
            dispatchButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    Toast.show('📡 Dispatching patrol unit...', 'success');
                });
            });

            const contactButtons = app.querySelectorAll('.btn-contact');
            contactButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    Toast.show('☎️ Calling user...', 'info');
                });
            });

            const quickActionButtons = app.querySelectorAll('.quick-action-btn');
            quickActionButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    Toast.show('⚡ Action triggered', 'info');
                });
            });
        },

        teardown() {
            const app = document.getElementById('app');
            if (app) app.innerHTML = '';
        }
    };

    // Role-aware page loader (inline pages)
    async function loadRolePage(role = 'user', params = {}) {
        try {
            const pages = {
                user: UserPage,
                guardian: GuardianPage,
                police: PolicePage
            };

            const page = pages[role];
            if (page && typeof page.init === 'function') {
                if (window.__safesphere_current_page && window.__safesphere_current_page.teardown) {
                    try { window.__safesphere_current_page.teardown(); } catch(e){}
                }
                window.__safesphere_current_page = page;
                page.init(params);
                console.log(`✅ Loaded role page: ${role}`);
            } else {
                console.warn(`Role page for '${role}' not found`);
            }
        } catch (err) {
            console.error('Failed to load role page', role, err);
        }
    }

    // Expose loader and setter globally for console/tools
    window.loadRolePage = loadRolePage;
    window.setRole = (r) => {
        localStorage.setItem('safesphere_role', r);
        document.body.dataset.role = r;
        loadRolePage(r, { role: r });
    };

    // Role switch UI
    (function createRoleSwitcher() {
        const roles = ['user', 'guardian', 'police'];
        const container = document.createElement('div');
        container.id = 'role-switcher';
        container.className = 'role-switcher';

        const label = document.createElement('label');
        label.className = 'role-switcher-label';
        label.textContent = '🔄 Role:';
        container.appendChild(label);

        const select = document.createElement('select');
        select.className = 'role-switcher-select';
        roles.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r;
            const icons = { user: '👤', guardian: '🛡️', police: '🚔' };
            opt.textContent = `${icons[r] || ''} ${r.charAt(0).toUpperCase() + r.slice(1)}`;
            select.appendChild(opt);
        });

        const currentRole = document.body.dataset.role || localStorage.getItem('safesphere_role') || 'user';
        select.value = currentRole;

        select.addEventListener('change', (e) => {
            const newRole = e.target.value;
            window.setRole(newRole);
            Toast.show(`Switched to ${newRole.toUpperCase()} role`, 'info', 2000);
            // Scroll to top when switching roles
            setTimeout(() => window.scrollTo(0, 0), 100);
        });

        container.appendChild(select);
        document.body.appendChild(container);
    })();

    // Determine role: prefer body[data-role] then localStorage, default 'user'
    const role = document.body.dataset.role || localStorage.getItem('safesphere_role') || 'user';
    loadRolePage(role, { role });

    console.log('✅ SafeSphere online!');
} catch (error) {
    console.error('Error:', error);
}

// ============================================
// SERVICE WORKER (Optional PWA support)
// ============================================

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Service worker registration can be added here if needed
    });
}
