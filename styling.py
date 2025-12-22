"""
Professional Banking UI Styling Module
Modern Banking Aesthetic - Deep Navy, Slate, Cyan with Glassmorphism
Different color schemes for different pages
"""

BANKING_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Public+Sans:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Default/Landing Page Background */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    background-attachment: fixed;
}

/* Landing Page Specific */
.stApp[data-page="landing"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* Login Page Background */
.stApp[data-page="login"] {
    background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #1e293b 100%);
}

/* Register Page Background */
.stApp[data-page="register"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* Admin Page Background */
.stApp[data-page="admin"] {
    background: linear-gradient(135deg, #1e293b 0%, #475569 50%, #1e293b 100%);
}

/* Status Check Page Background */
.stApp[data-page="status"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* Dashboard Page Background */
.stApp[data-page="dashboard"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
}

/* KYC Portal Background */
.stApp[data-page="kyc"] {
    background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #1e293b 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid rgba(6, 182, 212, 0.2);
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.1);
}

/* Glassmorphism Cards */
.glass-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 2rem;
    border: 1px solid rgba(6, 182, 212, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 1px rgba(6, 182, 212, 0.5);
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: rgba(6, 182, 212, 0.6);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 2px rgba(6, 182, 212, 0.8);
    transform: translateY(-2px);
}

.bank-header-main {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    padding: 3rem 0;
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 1px rgba(6, 182, 212, 0.5);
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(6, 182, 212, 0.3);
}

.bank-header-main::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.1), transparent);
    animation: shimmer-header 3s infinite;
}

@keyframes shimmer-header {
    0% { left: -100%; }
    100% { left: 100%; }
}

@keyframes shimmer {
    0% { transform: rotate(0deg); opacity: 0.3; }
    50% { transform: rotate(180deg); opacity: 0.6; }
    100% { transform: rotate(360deg); opacity: 0.3; }
}

.bank-logo {
    font-size: 3.5rem;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 0 0 20px rgba(6, 182, 212, 0.5), 2px 2px 8px rgba(0, 0, 0, 0.5);
    letter-spacing: 3px;
    margin: 0;
    font-family: 'Inter', sans-serif;
}

.bank-tagline {
    color: #06b6d4;
    font-size: 1.3rem;
    font-weight: 500;
    margin-top: 0.5rem;
    text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.professional-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 2rem;
    border: 1px solid rgba(6, 182, 212, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 1px rgba(6, 182, 212, 0.5);
    margin-bottom: 1.5rem;
}

.form-container {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 2.5rem;
    border: 1px solid rgba(6, 182, 212, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 1px rgba(6, 182, 212, 0.5);
}

.mandatory-field {
    color: #06b6d4;
    font-weight: 700;
    text-shadow: 0 0 5px rgba(6, 182, 212, 0.5);
}

.stButton>button {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2rem;
    font-weight: 700;
    font-size: 1rem;
    box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4), 0 0 1px rgba(6, 182, 212, 0.6);
    transition: all 0.3s ease;
}

.stButton>button:hover {
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.6), 0 0 2px rgba(6, 182, 212, 0.8);
    transform: translateY(-2px);
}

/* Logo Styles */
.ti-tans-logo-main {
    position: relative;
    transition: transform 0.3s ease;
    filter: drop-shadow(0 0 10px rgba(6, 182, 212, 0.5));
}

.ti-tans-logo-main:hover {
    transform: scale(1.05) rotate(5deg);
    filter: drop-shadow(0 0 15px rgba(6, 182, 212, 0.8));
}

.ti-tans-logo {
    position: relative;
    transition: transform 0.3s ease;
    filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.4));
}

.ti-tans-logo:hover {
    transform: scale(1.1);
    filter: drop-shadow(0 0 12px rgba(6, 182, 212, 0.6));
}

/* Animated Marquee for Offers */
.offers-marquee {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 1rem;
    border: 1px solid rgba(6, 182, 212, 0.3);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 1px rgba(6, 182, 212, 0.5);
    overflow: hidden;
    position: relative;
    margin: 1rem 0;
}

.marquee-content {
    display: flex;
    animation: marquee-scroll 15s linear infinite;
    white-space: nowrap;
}

.marquee-item {
    padding: 0.5rem 2rem;
    color: #06b6d4;
    font-weight: 600;
    text-shadow: 0 0 10px rgba(6, 182, 212, 0.6);
    font-size: 1rem;
    transition: all 0.3s ease;
    flex-shrink: 0;
}

.marquee-item:hover {
    color: #ffffff;
    text-shadow: 0 0 15px rgba(6, 182, 212, 0.9);
}

@keyframes marquee-scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

/* Statistics Section */
.stats-section {
    background: rgba(15, 23, 42, 0.9);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 3rem 2rem;
    border: 1px solid rgba(6, 182, 212, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 1px rgba(6, 182, 212, 0.5);
}

.stat-number {
    font-size: 3.5rem;
    font-weight: 900;
    color: #06b6d4;
    text-shadow: 0 0 20px rgba(6, 182, 212, 0.8), 0 0 40px rgba(6, 182, 212, 0.4);
    margin: 0.5rem 0;
}

.stat-label {
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 500;
    margin-top: 0.5rem;
}

/* Service Cards */
.service-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2rem;
    border: 1px solid rgba(6, 182, 212, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 1px rgba(6, 182, 212, 0.5);
    transition: all 0.3s ease;
    text-align: center;
    cursor: pointer;
}

.service-card:hover {
    border-color: rgba(6, 182, 212, 0.6);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 2px rgba(6, 182, 212, 0.8);
    transform: translateY(-5px);
}

.service-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 10px rgba(6, 182, 212, 0.5));
}

/* Hero Image Wrapper */
.hero-image-wrapper {
    border-radius: 24px;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 1px rgba(6, 182, 212, 0.5);
    border: 1px solid rgba(6, 182, 212, 0.3);
}

/* Typography Hierarchy */
h1, h2, h3 {
    font-family: 'Inter', 'Public Sans', sans-serif;
    font-weight: 800;
    color: #ffffff;
}

h1 {
    font-size: 3rem;
    font-weight: 900;
    text-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
}

h2 {
    font-size: 2rem;
    font-weight: 700;
}

h3 {
    font-size: 1.5rem;
    font-weight: 600;
}

p, span, div {
    color: #e2e8f0;
}
"""

def get_banking_css():
    """Return the professional banking CSS"""
    return BANKING_CSS
