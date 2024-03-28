import streamlit as st
import os
from formatxt import format_text_from_pdf
from analyze import analyze_farb, summarize_farb

# Initialize session state for login status
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

def parse_users(users_string):
    users = users_string.split()
    users_dict = {}
    for user in users:
        username, password = user.split(':')
        users_dict[username] = password
    return users_dict

def verify_credentials(username, password):
    db = parse_users(os.getenv("USERS"))
    if username in db:
        return db[username] == password
    return False

def app_main():
    st.title('Tempest in a Teapot')
    username = st.session_state['current_user']

    st.header(f"Welcome {username}, here's your projects.")

    cache_dir = f"./cache/{username}"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    uploaded_files = [f for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f))]

    uploaded_file = st.file_uploader("Choose a PDF to upload:", type="pdf")

    if uploaded_file is not None:
        file_path = os.path.join(cache_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f'File "{uploaded_file.name}" uploaded successfully.')
        # Update the list of uploaded files
        uploaded_files = [f for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f))]

    # remove files that aren't .pdf
    uploaded_files = [f for f in uploaded_files if f.endswith(".pdf")]

    if uploaded_files:
        selected_file = st.radio("Select a file:", uploaded_files, index=len(uploaded_files) - 1)
    else:
        selected_file = None
        st.info("No files uploaded yet.")

    if selected_file:
        file_path = os.path.join(cache_dir, selected_file)
        text_file_path = os.path.join(cache_dir, f"{selected_file}.txt")

        if not os.path.exists(text_file_path):
            if st.button('Extract Text'):
                with st.spinner("Extracting... (this may take a while, don't close this page)"):
                    text_pages = format_text_from_pdf(file_path)
                    with open(text_file_path, "w") as f:
                        for page in text_pages:
                            f.write(page + "\n")
                st.success(f'File "{selected_file}" extracted successfully.')

        if os.path.exists(text_file_path):
            with open(text_file_path, "r") as f:
                processed_text = f.read()
            st.text_area("Extracted Text", processed_text)

            # make a copy of uploaded files that only contains ones that have a .txt version also
            extracted_files = [f for f in uploaded_files if os.path.exists(os.path.join(cache_dir, f"{f}.txt"))]

            # now they need to choose one file as the letter, and another file as the invoice
            letter_file = st.selectbox("Select the letter:", extracted_files)
            invoice_file = st.selectbox("Select the invoice:", extracted_files)

            if letter_file and invoice_file:
                letter_txt = os.path.join(cache_dir, f"{letter_file}.txt")
                invoice_txt = os.path.join(cache_dir, f"{invoice_file}.txt")
                if st.button('Analyze'):
                    with st.spinner("Analyzing... (this may take a while, don't close this page)"):
                        text_items = analyze_farb(letter_txt, invoice_txt)
                        summary = summarize_farb(letter_txt, text_items).replace("$", "\\$") # Escape dollar signs
                    st.success("Analysis complete.")
                    st.markdown(summary)
                    st.write(text_items)

if __name__ == "__main__":
    if not st.session_state['is_logged_in']:
        st.title("Login Page")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if verify_credentials(username, password):
                st.success("Login Successful!")
                st.session_state['is_logged_in'] = True
                st.session_state['current_user'] = username
                # You may want to redirect or refresh the page here to display the next section
            else:
                st.error("Invalid username or password. Please try again.")

    # If logged in, show the management UI
    if st.session_state['is_logged_in']:
        app_main()
