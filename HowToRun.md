# 🚀 How to Run This Flask Application

This guide provides **step-by-step** instructions on how to set up, install dependencies, and run this **Flask application** in:
- ✅ **GitHub Codespaces** (Cloud-based)

---

## **1️⃣ Prerequisites**
Before running this application, ensure you have:
- **Python 3.8+** installed (Recommended: Python 3.10 or later)
- **Git** installed
- **A GitHub account** (for Codespaces)

You can check if Python is installed by running:
```bash
python --version
or
python3 --version


2️⃣ Clone the Repository
📍 On GitHub Codespaces

    Open your repository in GitHub.
    Click on "Code" → "Codespaces" → "New Codespace".


3️⃣ Set Up Virtual Environment
    1.Create a virtual environment:
        python3 -m venv venv

    2.Activate the virtual environment:
    📍 On GitHub Codespaces
    Codespaces automatically sets up a virtual environment, but you can manually activate it:
        source venv/bin/activate


4️⃣ Install Dependencies
Once the virtual environment is activated, install required packages:
        pip install -r requirements.txt

If requirements.txt is missing, install Flask manually:
        pip install flask


5️⃣ Set Environment Variables

This Flask application requires an environment variable SECRET_KEY.
        export SECRET_KEY="your_secret_key"
The SECRET_KEY in a Flask application is used for session management, signing cookies, and securing sensitive operations. It should be a random, strong string to enhance security. 
Example for SECRET_KEY:
    1. Use a Random Key (Recommended)
    You can generate a secure key using Python:
    Run this command in your Codespace terminal:

    python3 -c "import secrets; print(secrets.token_hex(24))"

    This will generate a random 48-character hexadecimal string, such as:

    4b1f2c3d4e5a6b7c8d9e0f112233445566778899aabbccdd

    Then, export it in your terminal:

    export SECRET_KEY="4b1f2c3d4e5a6b7c8d9e0f112233445566778899aabbccdd"


    export FLASK_APP=app
    export FLASK_ENV=development
 
 6️⃣ Run the Flask Application
 📍 On GitHub Codespaces
  
  1.flask run --host=0.0.0.0 --port=8000
