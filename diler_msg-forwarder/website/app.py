import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
import json

# Page configuration
st.set_page_config(page_title="HaltiBot", layout="centered")

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'new_user_registered' not in st.session_state:
    st.session_state.new_user_registered = False
if 'admin_emails_list' not in st.session_state:
    st.session_state.admin_emails_list = None

with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    credentials='./config.yaml',
    cookie_name=config['cookie']['name'],
    cookie_key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)

# Helper functions for loading and saving configurations
def load_accounts():
    """Load DiLer configuration from accounts.json"""
    try:
        with open('../accounts.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_accounts(accounts):
    """Save DiLer configuration to accounts.json"""
    with open('../accounts.json', 'w', encoding='utf-8') as file:
        json.dump(accounts, file, indent=2, ensure_ascii=False)

def get_user_account(streamlit_username):
    """Get account configuration for a specific Streamlit user"""
    accounts = load_accounts()
    for account in accounts:
        if account.get('STREAMLIT_USERNAME') == streamlit_username:
            return account
    return None

def save_user_account(streamlit_username, diler_username, diler_password, receiving_emails):
    """Save or update account configuration for a Streamlit user"""
    accounts = load_accounts()
    
    # Find and update existing account or create new one
    account_found = False
    for account in accounts:
        if account.get('STREAMLIT_USERNAME') == streamlit_username:
            account['DILER_USERNAME'] = diler_username
            account['DILER_PASSWORD'] = diler_password
            account['TO_EMAIL_ADDRESS'] = [e.strip() for e in receiving_emails.split(',')]
            account_found = True
            break
    
    if not account_found:
        accounts.append({
            'STREAMLIT_USERNAME': streamlit_username,
            'DILER_USERNAME': diler_username,
            'DILER_PASSWORD': diler_password,
            'TO_EMAIL_ADDRESS': [e.strip() for e in receiving_emails.split(',')]
        })
    
    save_accounts(accounts)
    return True

def load_config():
    """Load config.yaml"""
    with open('./config.yaml') as file:
        return yaml.load(file, Loader=SafeLoader)

def save_config(config):
    """Save config.yaml"""
    with open('./config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def delete_user(username):
    """Delete a user from config.yaml"""
    try:
        current_config = load_config()
        if 'credentials' in current_config and 'usernames' in current_config['credentials']:
            if username in current_config['credentials']['usernames']:
                del current_config['credentials']['usernames'][username]
                save_config(current_config)
                return True
    except Exception as e:
        st.error(f"Error deleting user: {e}")
    return False

def main():
    """Main page after successful login"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Welcome to the protected area!")
        st.write(f'Welcome *{st.session_state.get("name")}*')
        st.write("This is the main content of the app.")
    
    # Navigation buttons
    col_settings, col_logout = st.columns(2)
    
    with col_settings:
        if st.button("⚙️ DiLer Bot Settings", use_container_width=True):
            st.session_state.page = 'settings'
            st.rerun()
    
    with col_logout:
        # Logout button
        if st.button("Logout", use_container_width=True):
            authenticator.logout()
            st.session_state.authentication_status = None
            st.session_state.page = 'login'
            st.rerun()

def new_user_page():
    """Registration page"""
    st.title("Register a new account")
    
    # Back to login button
    if st.button("← Back to Login"):
        st.session_state.page = 'login'
        st.session_state.new_user_registered = False
        st.rerun()
    
    st.write("Fill in the form below to create a new account:")
    
    try:
        email_of_registered_user, \
        username_of_registered_user, \
        name_of_registered_user = authenticator.register_user(
            pre_authorized=config['pre-authorized'],
            merge_username_email=True,
            password_hint=False
        )
        if email_of_registered_user:
            st.success(f'User "{name_of_registered_user}" registered successfully!')
            st.session_state.new_user_registered = True
            st.session_state.new_username = username_of_registered_user
            st.rerun()
    except Exception as e:
        st.error(f"Error during registration: {e}")

def validate_diler_credentials(username, password):
    """
    Placeholder function to validate Diler credentials.
    Later this will check the credentials against the actual Diler system.
    """
    # TODO: Implement actual Diler credential validation
    # For now, this is just a placeholder
    return True

def diler_credentials_page():
    """Page to collect Diler credentials after registration"""
    st.title("Diler Account Setup")
    st.write("Please enter your Diler credentials to complete the registration:")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Diler username input
        diler_username = st.text_input(
            label="Diler Username",
            placeholder="Enter your Diler username"
        )
        
        # Diler password input
        diler_password = st.text_input(
            label="Diler Password",
            type="password",
            placeholder="Enter your Diler password"
        )
        
        st.divider()
        
        # Submit button
        if st.button("Complete Setup", use_container_width=True):
            if diler_username and diler_password:
                # Validate Diler credentials
                if validate_diler_credentials(diler_username, diler_password):
                    st.success("Diler credentials verified successfully!")
                    st.info("Setup complete. Redirecting to login...")
                    
                    # Reset session state and return to login
                    st.session_state.new_user_registered = False
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error("Invalid Diler credentials. Please try again.")
            else:
                st.warning("Please enter both username and password.")
        
        # Option to go back
        if st.button("← Back to Registration", use_container_width=True):
            st.session_state.new_user_registered = False
            st.session_state.page = 'register'
            st.rerun()

def login_page():
    """Login page with option to register"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Login")
        
        # Login form
        try:
            authenticator.login(location='main')
        except Exception as e:
            st.error(e)
        
        # Check authentication status
        if st.session_state.get('authentication_status'):
            st.session_state.page = 'main'
            st.rerun()
        elif st.session_state.get('authentication_status') is False:
            st.error('Username/password is incorrect')
        elif st.session_state.get('authentication_status') is None:
            st.warning('Please enter your username and password')
        
        st.divider()
        
        # Register button
        st.write("Don't have an account?")
        if st.button("Register new account", use_container_width=True):
            st.session_state.page = 'register'
            st.rerun()

def config_page():
    """Settings/Configuration page for logged-in users"""
    st.title("⚙️ DiLer Bot Settings")
    
    # Back to main button
    if st.button("← Back to Home"):
        st.session_state.page = 'main'
        st.rerun()
    
    st.divider()
    
    username = st.session_state.get('username')
    user_roles = st.session_state.get('roles', [])
    
    # Section 1: DiLer Configuration (for all users)
    st.subheader("DiLer Email Bot Configuration")
    
    col1, col2, col3 = st.columns([1, 4, 1])
    
    # Load existing account data if available
    existing_account = get_user_account(username)
    
    with col2:
        diler_username = st.text_input(
            label="DiLer Username",
            placeholder="Enter your DiLer username",
            value=existing_account.get('DILER_USERNAME', '') if existing_account else ""
        )
        
        diler_password = st.text_input(
            label="DiLer Password",
            type="password",
            placeholder="Enter your DiLer password",
            value=existing_account.get('DILER_PASSWORD', '') if existing_account else ""
        )
        
        # Convert email list to comma-separated string
        emails_value = ", ".join(existing_account.get('TO_EMAIL_ADDRESS', [])) if existing_account else ""
        
        receiving_emails = st.text_input(
            label="Receiving Emails (comma-separated)",
            placeholder="user@example.com, another@example.com",
            value=emails_value
        )
        
        if st.button("Save DiLer Configuration", use_container_width=True):
            if diler_username and diler_password and receiving_emails:
                try:
                    save_user_account(username, diler_username, diler_password, receiving_emails)
                    st.success("DiLer configuration saved successfully!")
                except Exception as e:
                    st.error(f"Error saving configuration: {e}")
            else:
                st.warning("Please fill in all fields")
    
    st.divider()
    
    # Section 2: Admin Configuration (only for admin users)
    if user_roles and 'admin' in user_roles:
        st.subheader("👨‍💼 Admin Settings")
        
        col1, col2, col3 = st.columns([1, 4, 1])
        
        with col2:
            # Section 2a: Manage registered users
            st.write("### Registered Users:")
            
            current_config = load_config()
            users = current_config.get('credentials', {}).get('usernames', {})
            
            if users:
                for username, user_data in users.items():
                    col_user, col_email, col_delete = st.columns([2, 4, 1])
                    
                    with col_user:
                        st.write(f"👤 {username}")
                    with col_email:
                        email = user_data.get('email', 'N/A')
                        st.write(f"📧 {email}")
                    with col_delete:
                        if st.button("➖", key=f"delete_user_{username}", help="Delete this user"):
                            st.session_state[f"show_delete_modal_{username}"] = True
                        
                        # Show modal dialog for confirmation
                        if st.session_state.get(f"show_delete_modal_{username}", False):
                            @st.dialog(f"Delete User: {username}")
                            def confirm_delete(user_to_delete=username, user_email=email):
                                st.warning(f"Are you sure you want to delete user **{user_to_delete}**?")
                                st.info(f"📧 Email: {user_email}")
                                
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ Yes, delete", use_container_width=True):
                                        if delete_user(user_to_delete):
                                            st.session_state[f"show_delete_modal_{user_to_delete}"] = False
                                            st.success(f"User '{user_to_delete}' deleted successfully!")
                                            st.rerun()
                                with col_no:
                                    if st.button("❌ Cancel", use_container_width=True):
                                        st.session_state[f"show_delete_modal_{user_to_delete}"] = False
                                        st.rerun()
                            
                            confirm_delete()
            else:
                st.info("No users registered yet.")
            
            st.divider()
            
            # Section 2b: Allowed emails to register
            st.write("### Allowed emails to register:")
            
            # Load emails from config if not in session state
            if st.session_state.admin_emails_list is None:
                current_config = load_config()
                st.session_state.admin_emails_list = current_config.get('pre-authorized', [])
            
            # Display each email with a remove button
            emails_list = st.session_state.admin_emails_list.copy()
            
            for idx, email in enumerate(emails_list):
                col_email, col_remove = st.columns([4, 1])
                with col_email:
                    st.write(f"📧 {email}")
                with col_remove:
                    if st.button("➖", key=f"remove_{idx}", help="Remove this email"):
                        st.session_state.admin_emails_list.pop(idx)
                        st.rerun()
            
            
            # Add new email section
            st.write("**Add new email:**")
            col_input, col_add = st.columns([4, 1])
            
            with col_input:
                new_email = st.text_input(
                    label="New email",
                    placeholder="neuemail@example.com",
                    label_visibility="collapsed"
                )
            
            with col_add:
                #st.write("")  # Spacing
                if st.button("➕", help="Add this email"):
                    if new_email and new_email.strip():
                        if new_email.strip() not in st.session_state.admin_emails_list:
                            st.session_state.admin_emails_list.append(new_email.strip())
                            st.rerun()
                        else:
                            st.warning("Email already exists!")
                    else:
                        st.warning("Please enter an email!")
            
            # Save button
            if st.button("Save Allowed Emails", use_container_width=True):
                try:
                    # Update config with the modified list
                    current_config = load_config()
                    current_config['pre-authorized'] = st.session_state.admin_emails_list
                    save_config(current_config)
                    
                    st.success("Admin settings saved successfully!")
                except Exception as e:
                    st.error(f"Error saving admin settings: {e}")

# Main app logic - route based on page state
try:
    if st.session_state.get('authentication_status'):
        # User is logged in
        if st.session_state.page == 'settings':
            config_page()
        elif st.session_state.page == 'main':
            main()
        else:
            # Force to main if logged in but on wrong page
            st.session_state.page = 'main'
            st.rerun()
    else:
        # User is not logged in
        if st.session_state.new_user_registered:
            # Show Diler credentials page after successful registration
            diler_credentials_page()
        elif st.session_state.page == 'register':
            new_user_page()
        else:
            # Default to login page
            login_page()
except Exception as e:
    st.error(f"An error occurred: {e}")

