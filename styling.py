"""
Professional Banking UI Styling Module
Chase/HSBC/Revolut inspired design - Deep Blues, Slate Greys, Clean Whites
"""

BANKING_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a1929 0%, #1a2332 50%, #0f1419 100%);
    background-attachment: fixed;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #1b263b 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.bank-header-main {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%);
    padding: 2rem 0;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.bank-logo {
    font-size: 3.5rem;
    font-weight: 800;
    color: #ffffff;
    text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);
    letter-spacing: 2px;
    margin: 0;
}

.bank-tagline {
    color: #e0e7ff;
    font-size: 1.2rem;
    font-weight: 400;
    margin-top: 0.5rem;
}

.professional-card {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 1.5rem;
}

.form-container {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.mandatory-field {
    color: #ef4444;
    font-weight: 600;
}

.stButton>button {
    background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
}
"""

def get_banking_css():
    """Return the professional banking CSS"""
    return BANKING_CSS

