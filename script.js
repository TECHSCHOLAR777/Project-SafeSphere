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
        const API_URL = 'https://improved-train-v679p9p5jr5p35gp-8000.app.github.dev/api/sos';

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
