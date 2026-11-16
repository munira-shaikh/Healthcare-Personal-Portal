 🏥 Healthcare Personal Portal
 Smart Patient Health Monitoring System

A web-based healthcare management application developed using Python Flask and MongoDB. It allows users to securely manage their personal health records through an organized and user-friendly dashboard.

📌 Project Overview

The Healthcare Personal Portal is designed to help users maintain and manage their personal healthcare information digitally. Users can register, log in, update their profiles, manage health records, upload medical documents, and view health-related reports.

 ✨ Key Features

- User Registration and Login
- Secure Password Hashing
- Personal Healthcare Dashboard
- Profile Management
- Password Change Functionality
- Add, View, Edit and Delete Health Records
- Medical Document Upload (PDF, JPG, JPEG, PNG)
- Health Risk Prediction Module
- Healthcare Reports Summary
- User Settings Page
- Responsive Navigation Sidebar

 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Framework |
| MongoDB | Database |
| PyMongo | Database Connectivity |
| HTML5 | Web Structure |
| CSS3 | Styling |
| JavaScript | Frontend Interactions |
| Jinja2 | Template Rendering |

 📂 Project Structure

```text
Healthcare-Personal-Portal/
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│
├── app.py
├── ml_model.py
├── requirements.txt
├── .gitignore
└── README.md
```

 ⚙️ Installation and Setup

 1. Clone the Repository

```bash
git clone https://github.com/munira-shaikh/Healthcare-Personal-Portal.git
```

 2. Open the Project Folder

```bash
cd Healthcare-Personal-Portal
```

 3. Create a Virtual Environment

```bash
python -m venv venv
```

 4. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

 5. Install Dependencies

```bash
pip install -r requirements.txt
```

 6. Configure MongoDB

Configure your MongoDB connection using the settings required by the application. Keep database credentials and secret keys private.

 7. Run the Application

```bash
python app.py
```

Open the local URL displayed by Flask in your browser.

 🚀 Future Enhancements

- Advanced Machine Learning Integration
- Improved Health Analytics Dashboard
- Enhanced Data Visualization
- Additional Healthcare Reporting Features

 👩‍💻 Developer

**Munira Shaikh**

GitHub: https://github.com/munira-shaikh

 ⚠️ Disclaimer

This project is developed for educational and demonstration purposes. Its health risk prediction output should not be considered a medical diagnosis or a substitute for professional medical advice.
