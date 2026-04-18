import os
import re
import pandas as pd
import streamlit as st


@st.cache_data
def load_uploaded_file(file):
    extension = os.path.splitext(file.name)[1].lower()

    if extension == ".csv":
        return pd.read_csv(file)

    elif extension == ".xlsx":
        return pd.read_excel(file)

    elif extension == ".json":
        return pd.read_json(file)

    else:
        raise ValueError("We currently only support .csv, .xlsx, or .json files. Please upload a dataset in one of these formats.")


def convert_google_sheet_url_to_csv(url: str) -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError("That doesn't look like a valid Google Sheets URL. Please copy the full link from your browser.")

    sheet_id = match.group(1)

    gid_match = re.search(r"gid=([0-9]+)", url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data
def load_google_sheet(url: str):
    csv_url = convert_google_sheet_url_to_csv(url)
    return pd.read_csv(csv_url)
