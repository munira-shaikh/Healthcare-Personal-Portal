HEALTHCARE PERSONAL PORTAL

This project is a Flask + MongoDB personal healthcare portal.

MAIN FEATURES
- User registration and login
- Secure password hashing
- Dashboard with live record counts
- Profile update
- Password change
- Health record add/view/edit/delete
- PDF/JPG/JPEG/PNG document upload
- Reports summary
- Settings page
- Common navigation between all authenticated pages
- Responsive sidebar on mobile

IMPORTANT FIX
The old health_record_document route expected a filename while the templates sent record_id.
The corrected application now uses:
/health-records/document/<record_id>

RUN
1. Open the project in Visual Studio Code.
2. Activate your existing venv.
3. Make sure MongoDB is running on 127.0.0.1:27017.
4. Install dependencies if required:
   pip install -r requirements.txt
5. Run:
   python app.py
6. Open:
   http://127.0.0.1:5000/

DATABASE
Database name: moon
Collections:
- users
- health_records

UPLOADS
Uploaded files are stored in static/uploads.
Allowed files: PDF, JPG, JPEG, PNG.
Maximum size: 10 MB.
