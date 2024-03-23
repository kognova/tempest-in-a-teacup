import streamlit as st
import os
from formatxt import format_text_from_pdf
from analyze import analyze_farb, summarize_farb

def app_main():
    st.title('Tempest in a Teapot')

    cache_dir = "./cache"
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
        text_file_path = os.path.join("./cache", f"{selected_file}.txt")

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
            extracted_files = [f for f in uploaded_files if os.path.exists(os.path.join("./cache", f"{f}.txt"))]

            # now they need to choose one file as the letter, and another file as the invoice
            letter_file = st.selectbox("Select the letter:", extracted_files)
            invoice_file = st.selectbox("Select the invoice:", extracted_files)

            if letter_file and invoice_file:
                letter_txt = os.path.join("./cache", f"{letter_file}.txt")
                invoice_txt = os.path.join("./cache", f"{invoice_file}.txt")
                if st.button('Analyze'):
                    with st.spinner("Analyzing... (this may take a while, don't close this page)"):
                        text_items = analyze_farb(letter_txt, invoice_txt)
                        summary = summarize_farb(letter_txt, text_items)
                    st.success("Analysis complete.")
                    st.markdown(summary)
                    st.write(text_items)

if __name__ == "__main__":
    app_main()