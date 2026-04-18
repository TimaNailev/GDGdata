# Call of Data | AI Financial Reporting Suite 🎖️

A high-performance, executive-grade data wrangling and financial reporting application tailored for GDG Tashkent.

## 🚀 Deployment Instructions

### 1. Requirements
Ensure you have Python 3.9+ installed and install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Secrets Management
The application requires a **Groq API Key** for Captain Price AI features.

- **Local Development**: Create a `.env` file in the root directory:
  ```env
  GROQ_API_KEY=your_key_here
  ```
- **Streamlit Cloud**: Add the secret to your deployment dashboard (Advanced Settings > Secrets):
  ```toml
  GROQ_API_KEY = "your_key_here"
  ```

### 3. File Assets
Ensure `logo.png` is present in the root directory for executive branding to function in PDF and Word exports.

## 📈 Key Features
- **AI Tactical Designer**: Automated report template generation.
- **Insightful Data Slices**: Automatic sorting of transactions by latest activity or top value.
- **Executive Exports**: Branded PDF and DOCX reports with synchronized data charts.
- **Strategic AI Insights**: Deep financial analysis using Llama 3.3.

---
*Specially made for GDG Tashkent 19th April*
