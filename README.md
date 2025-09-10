# 🎯 Face Attendance System

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18.2.0-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.1-green.svg)

**A modern, AI-powered attendance system using facial recognition technology**

Built with React frontend and Python FastAPI backend

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

The Face Attendance System is a cutting-edge solution that leverages facial recognition technology to automate attendance tracking. This system provides a seamless, contactless way to manage attendance in educational institutions, offices, or any organization requiring accurate time tracking.

### Key Highlights

- **Real-time Face Recognition**: Advanced AI-powered facial detection and recognition
- **Contactless Operation**: Safe and hygienic attendance marking
- **User-Friendly Interface**: Modern React-based web application
- **Comprehensive Logging**: Detailed attendance records with timestamps
- **Administrative Controls**: Admin panel for user management and data export
- **Cross-Platform**: Works on any device with a camera and web browser

---

## ✨ Features

### 🎭 Face Recognition
- **Multiple Face Detection Models**: Supports both HOG and CNN models for optimal accuracy
- **Advanced Image Enhancement**: CLAHE (Contrast Limited Adaptive Histogram Equalization) for better face detection
- **Robust Encoding**: 128-dimensional face encodings for accurate identification
- **Fallback Mechanisms**: Multiple detection strategies for challenging lighting conditions

### 👥 User Management
- **User Enrollment**: Easy registration with face photo capture
- **Multiple Face Samples**: Support for multiple face samples per user for improved accuracy
- **User Authentication**: Face-based login system
- **Profile Management**: Store additional user information (name, age, contact details)

### 📊 Attendance Tracking
- **Real-time Recognition**: Instant face matching and attendance marking
- **Comprehensive Logging**: CSV-based attendance logs with timestamps
- **Event Tracking**: Detailed logs of enrollment attempts, successful/failed authentications
- **Data Export**: Download attendance reports as ZIP files

### 🔧 Administrative Features
- **Admin Dashboard**: Complete system management interface
- **Data Management**: Clear all data functionality for testing/reset
- **Health Monitoring**: System health checks and user statistics
- **API Access**: RESTful API for integration with other systems

### 🎨 Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Intuitive Interface**: Clean, modern design with easy navigation
- **Real-time Feedback**: Instant visual feedback for all operations
- **Professional Styling**: Beautiful UI components and animations

---

## 🛠 Technology Stack

### Backend
- **🐍 Python 3.8+** - Core programming language
- **⚡ FastAPI** - Modern, fast web framework for building APIs
- **🤖 face-recognition** - Facial recognition library powered by dlib
- **📷 OpenCV** - Computer vision library for image processing
- **🔢 NumPy** - Numerical computing library
- **📊 Pandas** (for data processing)
- **🗃️ Pickle** - Data serialization for face encodings

### Frontend
- **⚛️ React 18.2.0** - Modern JavaScript UI library
- **📡 Axios** - HTTP client for API communication
- **🎨 CSS3** - Styling and animations
- **📱 Responsive Design** - Mobile-first approach

### Development Tools
- **🔧 Node.js & npm** - JavaScript runtime and package manager
- **🐍 pip** - Python package manager
- **📁 Git** - Version control system

---

## 📁 Project Structure

```
FaceAttendance-React-Python-/
├── 📂 backend/                 # Python FastAPI backend
│   ├── 📄 main.py             # Main FastAPI application
│   ├── 📄 requirements.txt    # Python dependencies
│   ├── 📂 db/                 # Face encodings storage (pickle files)
│   ├── 📂 logs/               # Attendance logs (CSV files)
│   └── 📂 snapshots/          # Saved face images
│
├── 📂 frontend/               # React frontend application
│   └── 📂 face-attendance-web-app-front/
│       ├── 📄 package.json   # Node.js dependencies
│       ├── 📂 src/           # React source code
│       │   ├── 📄 App.js     # Main React component
│       │   ├── 📄 MasterComponent.js  # Core UI component
│       │   └── 📄 API.js     # API communication layer
│       ├── 📂 public/        # Static assets
│       └── 📂 assets/        # UI images and resources
│
├── 📄 README.md              # Project documentation (this file)
├── 📄 LICENSE                # MIT License
└── 📄 .gitignore            # Git ignore rules
```

---

## 🚀 Installation

### Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.8 or higher** 📖 [Download Python](https://python.org/downloads/)
- **Node.js 14 or higher** 📖 [Download Node.js](https://nodejs.org/downloads/)
- **Git** 📖 [Download Git](https://git-scm.com/downloads/)
- **Camera** (webcam or external camera for face capture)

### 🔧 Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sridhar1030/FaceAttendance-React-Python-.git
   cd FaceAttendance-React-Python-
   ```

2. **Navigate to backend directory**
   ```bash
   cd backend
   ```

3. **Create a virtual environment** (recommended)
   ```bash
   python -m venv face_attendance_env
   
   # Activate virtual environment
   # On Windows:
   face_attendance_env\Scripts\activate
   # On macOS/Linux:
   source face_attendance_env/bin/activate
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   > **Note**: Installing `dlib` may take several minutes as it compiles from source. Ensure you have CMake installed if you encounter issues.

5. **Start the backend server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The backend API will be available at `http://localhost:8000`

### 🎨 Frontend Setup

1. **Open a new terminal** and navigate to frontend directory
   ```bash
   cd frontend/face-attendance-web-app-front
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

   The frontend application will be available at `http://localhost:3000`

### 🐳 Docker Setup (Optional)

For easier deployment, you can use Docker:

```bash
# Backend
cd backend
docker build -t face-attendance-backend .
docker run -p 8000:8000 face-attendance-backend

# Frontend
cd frontend/face-attendance-web-app-front
docker build -t face-attendance-frontend .
docker run -p 3000:3000 face-attendance-frontend
```

---

## 📖 Usage

### 🎯 Getting Started

1. **Start both servers** (backend on port 8000, frontend on port 3000)
2. **Open your browser** and navigate to `http://localhost:3000`
3. **Allow camera permissions** when prompted

### 👤 User Registration

1. Click on **"Register New User"** button
2. Fill in user details:
   - Username (required)
   - Full Name
   - Age
   - Contact Information
   - Email
3. **Capture face photo** using the camera interface
4. Click **"Register"** to save the user

> **💡 Tip**: For better recognition accuracy, capture multiple photos of the same user from different angles

### 🔐 Attendance Marking

1. Click on **"Mark Attendance"** or **"Login"**
2. **Position your face** in front of the camera
3. The system will automatically:
   - Detect your face
   - Match against registered users
   - Mark attendance if recognized
   - Display welcome message with user details

### 📊 Administrative Features

#### View Attendance Logs
- Click on **"Download Logs"** to export attendance data
- Logs include timestamps, events, user information, and match status

#### System Management
- Access admin panel for user management
- Clear all data for testing purposes
- Monitor system health and statistics

---

## 🔧 API Documentation

The backend provides a comprehensive RESTful API. Once the server is running, you can access:

- **Interactive API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative API Docs**: `http://localhost:8000/redoc` (ReDoc)

### 🚀 Key Endpoints

#### Health Check
```http
GET /health
```
Returns system status and registered user count.

#### User Enrollment
```http
POST /enroll
Content-Type: multipart/form-data

Parameters:
- userName: string (required)
- file: image file (required)
- fullName: string (optional)
- age: string (optional)
- contact: string (optional)
- email: string (optional)
```

#### Face Recognition/Authentication
```http
POST /search
Content-Type: multipart/form-data

Parameters:
- file: image file (required)
```

Or with JSON:
```http
POST /search
Content-Type: application/json

{
  "embedding": [128-dimensional array],
  "threshold": 0.6
}
```

#### Face Embedding Extraction
```http
POST /embed
Content-Type: multipart/form-data

Parameters:
- file: image file (required)
```
Returns 128-dimensional face embedding vector.

#### Download Attendance Logs
```http
GET /get_attendance_logs
```
Returns ZIP file containing attendance CSV logs.

#### Clear All Data (Admin)
```http
DELETE /admin/clear_all
```
⚠️ **Warning**: This endpoint deletes all user data and logs. Use with caution!

---

## ⚙️ Configuration

### Backend Configuration

Key parameters can be configured in `main.py`:

```python
# Face recognition tolerance (lower = more strict)
FACE_RECOGNITION_TOLERANCE = 0.6

# Detection models
DETECTION_MODEL = "hog"  # or "cnn" for better accuracy (slower)

# Image enhancement
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)
```

### Frontend Configuration

API endpoint configuration in `src/API.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Backend configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True

# Database configuration
DB_PATH=./db
LOGS_PATH=./logs
SNAPSHOTS_PATH=./snapshots
```

---


### 🛠 Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** with clear, commented code
5. **Test thoroughly** to ensure nothing breaks
6. **Commit your changes**
   ```bash
   git commit -m "Add: your feature description"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a Pull Request** with a clear description

### 📋 Contribution Guidelines

- **Code Style**: Follow PEP 8 for Python and ESLint rules for JavaScript
- **Documentation**: Update README and add inline comments for complex logic
- **Testing**: Ensure all existing functionality continues to work
- **Commit Messages**: Use clear, descriptive commit messages
- **Issue Reports**: Use GitHub Issues for bug reports and feature requests

### 🐛 Bug Reports

When reporting bugs, please include:
- **Environment details** (OS, Python/Node versions)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Screenshots** if applicable
- **Console logs** for errors

### 💡 Feature Requests

For new features, please:
- **Check existing issues** to avoid duplicates
- **Describe the use case** and benefits
- **Provide implementation ideas** if possible
- **Consider backward compatibility**

---

<div align="center">

**⭐ If you find this project useful, please consider giving it a star! ⭐**

**Made with ❤️ by the Face Attendance System Team**

</div>
