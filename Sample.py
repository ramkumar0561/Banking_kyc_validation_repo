import streamlit as st
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Titans Bank | Next-Gen Banking", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;900&display=swap');

* { font-family: 'Poppins', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
}

.main-header {
    color: #ffffff;
    font-size: 4rem;
    font-weight: 900;
    text-align: center;
    text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
    letter-spacing: 3px;
}

.tagline {
    text-align: center;
    color: #f0f0f0;
    font-size: 1.4rem;
    font-weight: 300;
    margin-bottom: 40px;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
}

.logo-container {
    text-align: center;
    margin: 20px 0;
}

.logo-text {
    font-size: 70px;
    font-weight: 900;
    color: #667eea;
    background: white;
    padding: 10px 35px;
    border-radius: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}

.service-card {
    background: rgba(255,255,255,0.95);
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    min-height: 200px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    transition: transform 0.3s ease;
    border: 2px solid transparent;
}

.service-card:hover {
    transform: translateY(-10px);
    border: 2px solid #667eea;
}

.service-icon {
    font-size: 3.5rem;
    margin-bottom: 15px;
}

.service-title {
    color: #764ba2;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 10px 0;
}

.service-desc {
    color: #555;
    font-size: 0.95rem;
}

.cta-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 40px;
    border-radius: 50px;
    font-size: 1.1rem;
    font-weight: 600;
    border: none;
    box-shadow: 0 5px 15px rgba(102,126,234,0.4);
}

.hero-box {
    background: rgba(255,255,255,0.95);
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.stats-box {
    background: rgba(255,255,255,0.9);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.offer-banner {
    background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    font-size: 1.2rem;
    font-weight: 600;
    margin: 20px 0;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

.section-title {
    color: white;
    font-size: 2.5rem;
    font-weight: 700;
    text-align: center;
    margin: 40px 0 30px 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.nav-menu {
    background: rgba(255,255,255,0.95);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

.product-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    margin: 10px 0;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    border-left: 5px solid #667eea;
}

.testimonial-card {
    background: rgba(255,255,255,0.9);
    padding: 25px;
    border-radius: 15px;
    margin: 10px 0;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    font-style: italic;
}

.footer {
    background: rgba(0,0,0,0.3);
    color: white;
    padding: 30px;
    border-radius: 15px;
    margin-top: 50px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "view" not in st.session_state:
    st.session_state.view = "Landing"
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None


def change_view(v):
    st.session_state.view = v
    st.rerun()


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<div class='logo-container'><span class='logo-text'>T</span></div>", unsafe_allow_html=True)
    st.markdown("### 🌟 Quick Access")

    if st.button("🏠 Home", use_container_width=True):
        change_view("Landing")
    if st.button("💼 Personal Banking", use_container_width=True):
        change_view("Personal")
    if st.button("💳 Cards & Payments", use_container_width=True):
        change_view("Cards")
    if st.button("📊 Investments", use_container_width=True):
        change_view("Investments")
    if st.button("🎁 Offers", use_container_width=True):
        change_view("Offers")
    if st.button("❓ Help & Support", use_container_width=True):
        change_view("Help")

    st.markdown("---")
    st.info("🔒 Secured by Titans AI Guardian")
    st.markdown("📞 **24/7 Support**\n1-800-TITANS-99")

# --- LANDING PAGE ---
if st.session_state.view == "Landing":
    st.markdown("<p class='main-header'>TITANS BANK</p>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Experience Banking Reimagined | Join 5M+ Happy Customers</p>",
                unsafe_allow_html=True)

    # Quick Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔐 Login", use_container_width=True):
            change_view("Login")
    with col2:
        if st.button("✨ Open Account", use_container_width=True):
            change_view("Register")
    with col3:
        if st.button("💰 Apply for Loan", use_container_width=True):
            st.info("Loan application coming soon!")
    with col4:
        if st.button("📱 Download App", use_container_width=True):
            st.success("Available on iOS & Android!")

    # Offer Banner
    st.markdown("""
    <div class='offer-banner'>
        🎉 LIMITED TIME OFFER: Get 0% Interest for 6 Months on Balance Transfer | Flat ₹500 Cashback on New Accounts!
    </div>
    """, unsafe_allow_html=True)

    # Main Services Grid
    st.markdown("<p class='section-title'>Banking Services</p>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>🏦</div>
            <div class='service-title'>Personal Banking</div>
            <p class='service-desc'>Savings, Current Accounts & More</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore", key="personal", use_container_width=True):
            change_view("Personal")

    with col2:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>💳</div>
            <div class='service-title'>Credit Cards</div>
            <p class='service-desc'>Rewards, Cashback & Travel Benefits</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore", key="credit", use_container_width=True):
            change_view("Cards")

    with col3:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>💎</div>
            <div class='service-title'>Debit Cards</div>
            <p class='service-desc'>Contactless & Secure Payments</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore", key="debit", use_container_width=True):
            change_view("Cards")

    with col4:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>🌐</div>
            <div class='service-title'>Net Banking</div>
            <p class='service-desc'>24/7 Online Access & Payments</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Explore", key="netbank", use_container_width=True):
            st.info("Login to access Net Banking")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>🏠</div>
            <div class='service-title'>Home Loans</div>
            <p class='service-desc'>Rates starting at 6.5% p.a.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Apply Now", key="home", use_container_width=True):
            st.success("Application form loading...")

    with col2:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>📈</div>
            <div class='service-title'>Investment Plans</div>
            <p class='service-desc'>Mutual Funds, Stocks & Bonds</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Invest Now", key="invest", use_container_width=True):
            change_view("Investments")

    with col3:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>💰</div>
            <div class='service-title'>Fixed Deposits</div>
            <p class='service-desc'>Guaranteed Returns up to 7.5%</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start FD", key="fd", use_container_width=True):
            st.info("Minimum deposit: ₹10,000")

    with col4:
        st.markdown("""
        <div class='service-card'>
            <div class='service-icon'>🛡️</div>
            <div class='service-title'>Insurance</div>
            <p class='service-desc'>Life, Health & Asset Protection</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Quote", key="insurance", use_container_width=True):
            st.success("Insurance advisor will contact you!")

    # Stats Section
    st.markdown("<p class='section-title'>Why Choose Titans Bank?</p>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='stats-box'>
            <h2 style='color: #667eea; margin: 0;'>5M+</h2>
            <p style='color: #555; margin: 5px 0;'>Active Customers</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='stats-box'>
            <h2 style='color: #667eea; margin: 0;'>2,500+</h2>
            <p style='color: #555; margin: 5px 0;'>Branches Nationwide</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='stats-box'>
            <h2 style='color: #667eea; margin: 0;'>4.9★</h2>
            <p style='color: #555; margin: 5px 0;'>Customer Rating</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class='stats-box'>
            <h2 style='color: #667eea; margin: 0;'>24/7</h2>
            <p style='color: #555; margin: 5px 0;'>Customer Support</p>
        </div>
        """, unsafe_allow_html=True)

    # Customer Testimonials
    st.markdown("<p class='section-title'>What Our Customers Say</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='testimonial-card'>
            <p>"Best banking experience! The app is incredibly smooth and customer service is top-notch."</p>
            <p style='text-align: right; font-weight: 600; margin-top: 15px;'>- Priya Sharma, Mumbai</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='testimonial-card'>
            <p>"Got my home loan approved in 48 hours. The interest rates are unbeatable!"</p>
            <p style='text-align: right; font-weight: 600; margin-top: 15px;'>- Rajesh Kumar, Delhi</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='testimonial-card'>
            <p>"Love the rewards program. Earned over ₹50,000 in cashback this year!"</p>
            <p style='text-align: right; font-weight: 600; margin-top: 15px;'>- Ananya Patel, Bangalore</p>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class='footer'>
        <p style='font-size: 1.2rem; font-weight: 600;'>Titans Bank - Banking Made Beautiful</p>
        <p>© 2025 Titans Bank. All Rights Reserved | Privacy Policy | Terms & Conditions</p>
        <p>📧 support@titansbank.com | 📞 1-800-TITANS-99</p>
    </div>
    """, unsafe_allow_html=True)

# --- PERSONAL BANKING PAGE ---
elif st.session_state.view == "Personal":
    st.markdown("<p class='section-title'>💼 Personal Banking Solutions</p>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Savings Accounts", "Current Accounts", "Deposits", "Online Banking"])

    with tab1:
        st.markdown("### 💰 Savings Account Options")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class='product-card'>
                <h3>🌟 Titans Classic Savings</h3>
                <p><strong>Interest Rate:</strong> 4.5% p.a.</p>
                <p><strong>Minimum Balance:</strong> ₹5,000</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Free debit card</li>
                    <li>Unlimited ATM withdrawals</li>
                    <li>Mobile & Net Banking</li>
                    <li>Cheque book facility</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open Classic Account", use_container_width=True):
                change_view("Register")

        with col2:
            st.markdown("""
            <div class='product-card'>
                <h3>👑 Titans Premium Savings</h3>
                <p><strong>Interest Rate:</strong> 6.0% p.a.</p>
                <p><strong>Minimum Balance:</strong> ₹50,000</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Premium debit card with lounge access</li>
                    <li>Personal relationship manager</li>
                    <li>Zero forex markup</li>
                    <li>Exclusive investment opportunities</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Open Premium Account", use_container_width=True):
                change_view("Register")

    with tab2:
        st.markdown("### 🏢 Current Accounts for Businesses")
        st.write("Perfect for entrepreneurs and business owners")

        account_type = st.selectbox(
            "Select Business Type",
            ["Sole Proprietorship", "Partnership", "Private Limited", "Public Limited", "LLP"]
        )

        col1, col2 = st.columns(2)
        with col1:
            st.info(
                "✅ Free unlimited transactions\n✅ Overdraft facility\n✅ Multi-user access\n✅ Cash management services")
        with col2:
            st.success(
                "📊 Business analytics dashboard\n📱 Mobile banking for business\n💼 Trade finance solutions\n🌐 International payments")

        if st.button("Apply for Current Account", use_container_width=True):
            st.success("Business account application initiated!")

    with tab3:
        st.markdown("### 💎 Deposit Products")

        deposit_type = st.radio("Choose Deposit Type", ["Fixed Deposit", "Recurring Deposit", "Tax Saving FD"],
                                horizontal=True)

        if deposit_type == "Fixed Deposit":
            st.markdown("""
            <div class='product-card'>
                <h3>🔒 Fixed Deposit Rates</h3>
                <p><strong>7 days - 45 days:</strong> 3.5% p.a.</p>
                <p><strong>46 days - 6 months:</strong> 5.5% p.a.</p>
                <p><strong>6 months - 1 year:</strong> 6.5% p.a.</p>
                <p><strong>1 year - 5 years:</strong> 7.5% p.a.</p>
                <p><strong>Senior Citizens:</strong> Additional 0.5% p.a.</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                deposit_amount = st.number_input("Deposit Amount (₹)", min_value=10000, value=100000, step=10000)
            with col2:
                tenure = st.selectbox("Tenure", ["3 months", "6 months", "1 year", "2 years", "3 years", "5 years"])

            if st.button("Calculate Returns", use_container_width=True):
                st.success(f"Estimated Maturity Value: ₹{deposit_amount * 1.075:.2f}")

    with tab4:
        st.markdown("### 🌐 Online & Mobile Banking")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class='service-card'>
                <div class='service-icon'>💻</div>
                <h4>Net Banking</h4>
                <p>Full account access from browser</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='service-card'>
                <div class='service-icon'>📱</div>
                <h4>Mobile App</h4>
                <p>Banking on the go</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class='service-card'>
                <div class='service-icon'>⌚</div>
                <h4>Smartwatch</h4>
                <p>Quick transactions</p>
            </div>
            """, unsafe_allow_html=True)

        st.info("🔐 **Security Features:** Biometric login | OTP verification | Transaction alerts | Device management")

    if st.button("⬅ Back to Home", use_container_width=True):
        change_view("Landing")

# --- CARDS PAGE ---
elif st.session_state.view == "Cards":
    st.markdown("<p class='section-title'>💳 Cards & Payment Solutions</p>", unsafe_allow_html=True)

    card_tab = st.radio("Select Card Type", ["Credit Cards", "Debit Cards", "Prepaid Cards"], horizontal=True)

    if card_tab == "Credit Cards":
        st.markdown("### 💎 Premium Credit Cards")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class='product-card'>
                <h3>🌟 Titans Cashback</h3>
                <p><strong>Annual Fee:</strong> ₹499</p>
                <p><strong>Cashback:</strong> 5% on all spends</p>
                <p><strong>Joining Bonus:</strong> ₹500</p>
                <hr>
                <p>✨ No category restrictions</p>
                <p>🎁 Monthly milestone rewards</p>
                <p>🛡️ Zero liability on fraud</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Apply Now", key="cc1", use_container_width=True):
                st.success("Application started!")

        with col2:
            st.markdown("""
            <div class='product-card'>
                <h3>✈️ Titans Travel</h3>
                <p><strong>Annual Fee:</strong> ₹2,999</p>
                <p><strong>Rewards:</strong> 10 points per ₹100</p>
                <p><strong>Lounge Access:</strong> Unlimited</p>
                <hr>
                <p>✨ Complimentary airport transfers</p>
                <p>🎁 Travel insurance up to ₹50L</p>
                <p>🛡️ Zero forex markup</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Apply Now", key="cc2", use_container_width=True):
                st.success("Application started!")

        with col3:
            st.markdown("""
            <div class='product-card'>
                <h3>👑 Titans Platinum</h3>
                <p><strong>Annual Fee:</strong> ₹10,000</p>
                <p><strong>Rewards:</strong> 25 points per ₹100</p>
                <p><strong>Credit Limit:</strong> Up to ₹25L</p>
                <hr>
                <p>✨ Personal concierge service</p>
                <p>🎁 Golf privileges worldwide</p>
                <p>🛡️ Exclusive lifestyle benefits</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Apply Now", key="cc3", use_container_width=True):
                st.success("Application started!")

    elif card_tab == "Debit Cards":
        st.markdown("### 💎 Debit Card Variants")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class='product-card'>
                <h3>💳 Titans Classic Debit</h3>
                <p><strong>Annual Fee:</strong> FREE</p>
                <p><strong>Daily Limit:</strong> ₹50,000</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Contactless payments</li>
                    <li>Free ATM withdrawals</li>
                    <li>1% cashback on UPI</li>
                    <li>EMI conversion facility</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='product-card'>
                <h3>👑 Titans Premium Debit</h3>
                <p><strong>Annual Fee:</strong> ₹199</p>
                <p><strong>Daily Limit:</strong> ₹2,00,000</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Airport lounge access (4/year)</li>
                    <li>Unlimited ATM withdrawals</li>
                    <li>2% cashback on all spends</li>
                    <li>Global acceptance</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("### 🎁 Prepaid Cards")
        st.info("💡 Perfect for gifting, travel, and controlled spending!")

        st.write("**Features:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("✅ Load up to ₹2,00,000\n✅ Multi-currency support\n✅ No credit check required")
        with col2:
            st.write("✅ Instant activation\n✅ Reloadable anytime\n✅ Track spending via app")

    if st.button("⬅ Back to Home", use_container_width=True):
        change_view("Landing")

# --- INVESTMENTS PAGE ---
elif st.session_state.view == "Investments":
    st.markdown("<p class='section-title'>📈 Investment & Wealth Management</p>", unsafe_allow_html=True)

    invest_tab = st.radio("", ["Mutual Funds", "Stocks & Trading", "Insurance Plans", "Gold & Commodities"],
                          horizontal=True)

    if invest_tab == "Mutual Funds":
        st.markdown("### 💼 Curated Mutual Fund Portfolio")

        risk_profile = st.select_slider("Select Your Risk Profile",
                                        options=["Conservative", "Moderate", "Balanced", "Aggressive",
                                                 "Very Aggressive"])

        st.write(f"**Recommended funds for {risk_profile} investors:**")

        if risk_profile in ["Conservative", "Moderate"]:
            st.markdown("""
            <div class='product-card'>
                <h4>🛡️ Titans Liquid Fund</h4>
                <p><strong>Returns:</strong> 6.5% p.a. | <strong>Risk:</strong> Low</p>
                <p>Ideal for short-term goals and emergency funds</p>
            </div>
            """, unsafe_allow_html=True)

        if risk_profile in ["Balanced", "Aggressive", "Very Aggressive"]:
            st.markdown("""
            <div class='product-card'>
                <h4>📊 Titans Equity Growth Fund</h4>
                <p><strong>Returns:</strong> 15% p.a. (3 yr) | <strong>Risk:</strong> High</p>
                <p>Long-term wealth creation through equity markets</p>
            </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            sip_amount = st.number_input("Monthly SIP Amount (₹)", min_value=500, value=5000, step=500)
        with col2:
            duration = st.selectbox("Investment Duration", ["1 year", "3 years", "5 years", "10 years", "15 years"])

        if st.button("Calculate Returns", use_container_width=True):
            years = int(duration.split()[0])
            total_investment = sip_amount * 12 * years
            estimated_returns = total_investment * 1.12 ** years
            st.success(
                f"💰 **Projected Value:** ₹{estimated_returns:,.0f}\n\n**Total Investment:** ₹{total_investment:,.0f}")

    elif invest_tab == "Stocks & Trading":
        st.markdown("### 📊 Stock Trading Platform")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("NIFTY 50", "22,453", "+127 (+0.57%)")
        with col2:
            st.metric("SENSEX", "74,119", "+203 (+0.28%)")
        with col3:
            st.metric("USD/INR", "83.42", "-0.15 (-0.18%)")

        st.info("🚀 **Zero brokerage** on equity delivery trades | **Flat ₹20** on intraday")

        trading_account = st.selectbox("Choose Account Type", ["Basic Trading", "Pro Trader", "Algo Trading"])

        if st.button("Open Trading Account", use_container_width=True):
            st.success("Trading account application submitted!")

    elif invest_tab == "Insurance Plans":
        st.markdown("### 🛡️ Insurance Solutions")

        insurance_type = st.radio("", ["Term Insurance", "Health Insurance", "Car Insurance", "Home Insurance"],
                                  horizontal=True)

        if insurance_type == "Term Insurance":
            st.write("**Get coverage up to ₹2 Crore**")
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Your Age", min_value=18, max_value=65, value=30)
                coverage = st.selectbox("Coverage Amount", ["₹50 Lakhs", "₹1 Crore", "₹2 Crores"])
            with col2:
                term = st.selectbox("Policy Term", ["20 years", "30 years", "Until 60 years"])
                st.metric("Estimated Premium", f"₹{age * 150}/month")

        elif insurance_type == "Health Insurance":
            st.write("**Family Floater & Individual Plans**")
            family_size = st.radio("Plan Type", ["Individual", "Family (4 members)", "Senior Citizen"], horizontal=True)
            cover_amount = st.select_slider("Sum Insured", options=["₹5L", "₹10L", "₹25L", "₹50L", "₹1Cr"])
            st.info(
                "✅ Cashless hospitalization at 10,000+ hospitals\n✅ No room rent limit\n✅ Pre & post hospitalization covered")

    else:
        st.markdown("### 🪙 Gold & Commodities Investment")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class='product-card'>
                <h4>✨ Digital Gold</h4>
                <p><strong>Current Price:</strong> ₹6,420/gram</p>
                <p>Buy & sell 24K gold anytime</p>
                <p>Zero making charges | Doorstep delivery</p>
            </div>
            """, unsafe_allow_html=True)
            gold_grams = st.number_input("Buy Gold (grams)", min_value=0.5, value=10.0, step=0.5)
            if st.button("Buy Gold Now", use_container_width=True):
                st.success(f"Purchased {gold_grams}g gold worth ₹{gold_grams * 6420:,.0f}")

        with col2:
            st.markdown("""
            <div class='product-card'>
                <h4>💰 Silver Investment</h4>
                <p><strong>Current Price:</strong> ₹78,500/kg</p>
                <p>Invest in 99.9% pure silver</p>
                <p>Secure vault storage available</p>
            </div>
            """, unsafe_allow_html=True)
            silver_kg = st.number_input("Buy Silver (kg)", min_value=0.1, value=1.0, step=0.1)
            if st.button("Buy Silver Now", use_container_width=True):
                st.success(f"Purchased {silver_kg}kg silver worth ₹{silver_kg * 78500:,.0f}")

    if st.button("⬅ Back to Home", use_container_width=True):
        change_view("Landing")

# --- OFFERS PAGE ---
elif st.session_state.view == "Offers":
    st.markdown("<p class='section-title'>🎁 Exclusive Offers & Deals</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='offer-banner'>
            🎉 NEW YEAR SPECIAL
        </div>
        <div class='product-card'>
            <h3>Zero Annual Fee Forever!</h3>
            <p>Apply for Titans Cashback Credit Card before Dec 31st and enjoy lifetime free membership</p>
            <p><strong>Offer Code:</strong> TITANS2025</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='product-card'>
            <h3>🏠 Home Loan Festival</h3>
            <p><strong>6.5% p.a.</strong> flat rate</p>
            <p>✅ Zero processing fee<br>✅ Instant approval<br>✅ Up to 90% funding</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='offer-banner' style='background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);'>
            💰 DEPOSIT BONANZA
        </div>
        <div class='product-card'>
            <h3>7.5% on Fixed Deposits</h3>
            <p>Limited period offer on FDs above ₹1 Lakh</p>
            <p><strong>Valid till:</strong> December 31, 2025</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='product-card'>
            <h3>📱 App Download Rewards</h3>
            <p>Get <strong>₹200 cashback</strong> on your first UPI transaction</p>
            <p>Plus additional ₹100 on 5 transactions</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🛍️ Partner Merchant Offers")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='product-card'>
            <h4>🍔 Food & Dining</h4>
            <p>30% off on Swiggy, Zomato</p>
            <p>Max discount: ₹150</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='product-card'>
            <h4>🎬 Entertainment</h4>
            <p>Buy 1 Get 1 on movie tickets</p>
            <p>Valid on BookMyShow</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='product-card'>
            <h4>✈️ Travel Deals</h4>
            <p>Flat ₹3,000 off on flights</p>
            <p>₹2,000 off on hotels</p>
        </div>
        """, unsafe_allow_html=True)

    if st.button("⬅ Back to Home", use_container_width=True):
        change_view("Landing")

# --- REGISTRATION PAGE ---
elif st.session_state.view == "Register":
    st.markdown("<p class='section-title'>✨ Open Your Account Today</p>", unsafe_allow_html=True)

    with st.form("reg_form"):
        st.markdown("### 👤 Personal Information")
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full Name*")
            dob = st.date_input("Date of Birth*", min_value=datetime.date(1920, 1, 1))
        with c2:
            age = st.number_input("Age*", min_value=18, max_value=120)
            marital_status = st.selectbox("Marital Status*", ["Single", "Married", "Divorced", "Widowed"])

        address = st.text_area("Residential Address*")

        st.markdown("### 📄 Address Proof")
        doc_type = st.selectbox("Document Type*", ["Aadhaar", "PAN", "Passport", "Voter ID"])
        doc_file = st.file_uploader(f"Upload {doc_type}*", type=["pdf", "jpg", "png"])

        submitted = st.form_submit_button("Submit Application")

    st.markdown("### 📸 Photo Identification*")
    photo_mode = st.radio("Choose Identification Method", ["Upload a Photo", "Use Webcam"], horizontal=True)

    user_photo = None

    if photo_mode == "Upload a Photo":
        user_photo = st.file_uploader("Browse and upload your photo (JPG/PNG, Max 1MB)", type=["jpg", "jpeg", "png"])
        if user_photo and user_photo.size > 1 * 1024 * 1024:
            st.error("File size exceeds 1MB")
            user_photo = None

    elif photo_mode == "Use Webcam":
        st.info("📸 Allow camera access when prompted")
        user_photo = st.camera_input("Take a live photo")

    if submitted:
        if not full_name or not address or not doc_file or not user_photo:
            st.error("❌ Please complete all required fields and photo verification.")
        else:
            st.success(
                f"✅ Application submitted successfully!\n\nReference ID: TITAN-{datetime.datetime.now().strftime('%H%M%S')}")
            st.balloons()

    if st.button("⬅ Back to Home"):
        change_view("Landing")

# --- HELP PAGE ---
elif st.session_state.view == "Help":
    st.markdown("<p class='section-title'>🆘 Help & Support Center</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='stats-box'>
            <h3>📞</h3>
            <h4>Call Us</h4>
            <p>1-800-TITANS-99</p>
            <p style='font-size: 0.9rem;'>24/7 Available</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='stats-box'>
            <h3>📧</h3>
            <h4>Email Support</h4>
            <p>support@titansbank.com</p>
            <p style='font-size: 0.9rem;'>Response in 2 hours</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='stats-box'>
            <h3>💬</h3>
            <h4>Live Chat</h4>
            <p>Chat with AI Assistant</p>
            <p style='font-size: 0.9rem;'>Instant Replies</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📚 Frequently Asked Questions")

    with st.expander("How do I reset my password?"):
        st.write(
            "Click on 'Forgot Password' on the login page. Enter your registered email/mobile number and follow the OTP verification process.")

    with st.expander("What documents are needed for account opening?"):
        st.write(
            "You need: Valid ID proof (Aadhaar/PAN/Passport), Address proof, Recent photograph, and minimum deposit of ₹500.")

    with st.expander("How can I block my card?"):
        st.write(
            "Call our 24/7 helpline immediately at 1-800-TITANS-99 or use the 'Block Card' option in the mobile app.")

    with st.expander("What are the charges for online transfers?"):
        st.write("NEFT/RTGS/IMPS transfers are FREE for all account holders. No hidden charges.")

    with st.expander("How do I upgrade my account?"):
        st.write(
            "Visit your nearest branch or raise a request through net banking. Our team will contact you within 24 hours.")

    if st.button("⬅ Back to Home"):
        change_view("Landing")