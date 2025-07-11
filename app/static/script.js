// Web Client JavaScript for Appointment Manager
class AppointmentChat {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.sessionId = this.generateSessionId();
        this.isTyping = false;
        this.messageHistory = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeConnection();
        this.loadInitialData();
    }

    generateSessionId() {
        return 'web_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatForm = document.getElementById('chatForm');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.statusText = document.getElementById('statusText');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.totalAppointments = document.getElementById('totalAppointments');
        this.availableSlots = document.getElementById('availableSlots');
        this.initialTime = document.getElementById('initialTime');
        
        // Set initial timestamp
        this.initialTime.textContent = this.formatTime(new Date());
    }

    setupEventListeners() {
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.messageInput.addEventListener('keypress', (e) => this.handleKeyPress(e));
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        
        // Auto-resize textarea behavior
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
        
        // Focus on input when page loads
        window.addEventListener('load', () => {
            this.messageInput.focus();
        });
    }

    async initializeConnection() {
        try {
            this.updateConnectionStatus('connecting', 'Connecting...');
            
            // Test connection to health endpoint
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateConnectionStatus('online', 'Connected');
            } else {
                throw new Error('Service unhealthy');
            }
        } catch (error) {
            console.error('Connection failed:', error);
            this.updateConnectionStatus('offline', 'Connection Failed');
        }
    }

    async loadInitialData() {
        try {
            // Load basic statistics
            const statsResponse = await fetch(`${this.apiBaseUrl}/api/v1/stats`);
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                this.updateStats(stats);
            }
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }

    updateConnectionStatus(status, text) {
        this.connectionStatus.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }

    updateStats(stats) {
        if (stats.total_appointments !== undefined) {
            this.totalAppointments.textContent = stats.total_appointments;
        }
        if (stats.available_slots !== undefined) {
            this.availableSlots.textContent = stats.available_slots;
        }
    }

    handleSubmit(e) {
        e.preventDefault();
        const message = this.messageInput.value.trim();
        if (message && !this.isTyping) {
            this.sendMessage(message);
        }
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSubmit(e);
        }
    }

    handleInputChange() {
        // Enable/disable send button based on input
        const hasContent = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasContent || this.isTyping;
    }

    async sendMessage(message) {
        if (this.isTyping) return;
        
        this.isTyping = true;
        this.updateSendButton(false);
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.handleInputChange();
        
        // Show loading
        this.showLoading(true);
        
        try {
            // Send message to API
            const response = await fetch(`${this.apiBaseUrl}/api/v1/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_id: 'web_user',
                    platform: 'web'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Add bot response to chat
            this.addMessage(data.response, 'bot');
            
            // Update conversation history
            this.messageHistory.push({
                user: message,
                bot: data.response,
                timestamp: new Date()
            });
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, I encountered an error processing your message. Please try again.', 'bot', true);
        } finally {
            this.showLoading(false);
            this.isTyping = false;
            this.updateSendButton(true);
            this.messageInput.focus();
        }
    }

    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        if (isError) {
            messageContent.style.background = '#fee2e2';
            messageContent.style.color = '#dc2626';
            messageContent.style.border = '1px solid #fecaca';
        }
        
        // Convert newlines to paragraphs
        const paragraphs = content.split('\n').filter(p => p.trim()).map(p => `<p>${this.escapeHtml(p)}</p>`).join('');
        messageContent.innerHTML = paragraphs;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.innerHTML = `<span>${this.formatTime(new Date())}</span>`;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    updateSendButton(enabled) {
        this.sendButton.disabled = !enabled;
        if (enabled) {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
    }

    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.add('active');
        } else {
            this.loadingOverlay.classList.remove('active');
        }
    }

    // Quick action methods
    sendQuickMessage(message) {
        if (!this.isTyping) {
            this.messageInput.value = message;
            this.sendMessage(message);
        }
    }
}

// Quick action function for buttons
function sendQuickMessage(message) {
    if (window.appointmentChat) {
        window.appointmentChat.sendQuickMessage(message);
    }
}

// Initialize the chat when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.appointmentChat = new AppointmentChat();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.appointmentChat) {
        // Reconnect when page becomes visible
        window.appointmentChat.initializeConnection();
    }
});

// Add some utility functions
window.AppointmentUtils = {
    formatDate: (date) => {
        return date.toLocaleDateString([], {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    formatDateTime: (date) => {
        return date.toLocaleString([], {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    isBusinessHours: () => {
        const now = new Date();
        const hour = now.getHours();
        const day = now.getDay();
        
        // Monday to Friday: 9 AM to 6 PM
        // Saturday: 10 AM to 4 PM
        // Sunday: Closed
        
        if (day === 0) return false; // Sunday
        if (day >= 1 && day <= 5) return hour >= 9 && hour < 18; // Mon-Fri
        if (day === 6) return hour >= 10 && hour < 16; // Saturday
        
        return false;
    }
};

// Add some keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Alt + R to refresh connection
    if (e.altKey && e.key === 'r') {
        e.preventDefault();
        if (window.appointmentChat) {
            window.appointmentChat.initializeConnection();
        }
    }
    
    // Escape to clear input
    if (e.key === 'Escape' && document.activeElement === document.getElementById('messageInput')) {
        document.getElementById('messageInput').value = '';
        document.getElementById('messageInput').blur();
    }
});