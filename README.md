# VeerDrishti - AI-Powered Surveillance System

## 🏆 Hackathon Information
- **Event**: Nextech 1.0
- **Venue**: NMIET, Bhubaneswar
- **Team Name**: The Unstoppable
- **Institution**: Regional College of Management, Bhubaneswar

## 👥 Team Members
- **Rajeev Sritam Mohapatra** (Team Leader)
- **Debasmit Sahoo**
- **Soumya Ranjan Mishra**
- **Subhranshu Sekhar Pal**
- **Shivam Kumar Raj**

## 🎯 Project Overview
VeerDrishti is an intelligent surveillance system that combines computer vision, face recognition, and real-time monitoring to provide comprehensive security solutions. The system can identify and categorize individuals, monitor soldier vitals, and provide instant alerts for security threats.

## ✨ Key Features

### 🔍 Face Recognition & Classification
- **Real-time face detection** using OpenCV Haar Cascades
- **LBPH (Local Binary Patterns Histograms)** face recognition
- **Multi-category classification**:
  - 🟢 **Official** - Government officials and authorized personnel
  - 🟡 **Citizen** - Regular citizens and visitors
  - 🔴 **Criminal** - Known criminals and security threats
  - 🟠 **Intruder** - Unknown/unrecognized individuals

### 📊 Soldier Monitoring System
- **Real-time vital monitoring** (Heart Rate, GPS coordinates)
- **Dynamic activity simulation** (Rest, Patrol, Jog, Sprint, Engaged, Injured)
- **Status tracking** (OK, Warning, Critical)
- **Automated alerts** for critical conditions

### 🚨 Intelligent Alert System
- **Criminal detection alerts** with immediate notifications
- **Unknown person alerts** for security breaches
- **Critical soldier status alerts** for medical emergencies
- **Audio notifications** with browser-compatible sound system

### 📱 Modern Web Interface
- **Responsive design** optimized for mobile and desktop
- **Real-time video feed** with live annotations
- **Interactive face registration** with photo capture
- **Live soldier dashboard** with dynamic updates

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **OpenCV** - Computer vision and image processing
- **LBPH Face Recognizer** - Lightweight face recognition
- **HOG Descriptor** - Person detection
- **Haar Cascades** - Face detection
- **Threading** - Background processing for real-time operations

### Frontend
- **React** - Modern JavaScript framework
- **Tailwind CSS** - Utility-first CSS framework
- **Canvas API** - Real-time overlay rendering
- **Web Audio API** - Sound notifications

### Data Storage
- **File System** - Face crops and model storage
- **Pickle** - Serialization for label mappings
- **In-memory caching** - Real-time data storage

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- Webcam/Camera access

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📡 API Endpoints

### Core Endpoints
- `GET /api/frame.jpg` - Live camera feed with annotations
- `GET /api/detections` - Detection data with bounding boxes
- `GET /api/soldiers` - Soldier telemetry data
- `GET /api/faces` - Registered face IDs

### Face Registration
- `POST /api/register-face` - Register new faces with categories
  - Form data: `id`, `file`, `category` (citizen/official/criminal)

## 🎮 Usage Guide

### 1. Face Registration
1. Enter a unique ID for the person
2. Select category (Citizen/Official/Criminal)
3. Upload an image or capture from live feed
4. System automatically detects faces and trains the model

### 2. Real-time Monitoring
- Live video feed shows detected faces with color-coded bounding boxes
- Green: Official, Yellow: Citizen, Red: Criminal, Orange: Intruder
- Soldier cards display real-time vitals and status
- Alerts appear for security threats and critical conditions

### 3. Alert Management
- Enable sound notifications for better awareness
- Monitor alert history in the alerts panel
- Critical soldier status triggers immediate notifications

## 🔧 Configuration

### Camera Settings
- Default camera index: 0
- Resolution: 640x480 (optimized for performance)
- Frame rate: ~2 FPS for real-time processing

### Recognition Parameters
- LBPH threshold: 85.0 (adjustable for accuracy vs. recall)
- Face detection: Haar Cascades with optimized parameters
- Person detection: HOG Descriptor with stride optimization

## 📈 Performance Optimizations

### Backend Optimizations
- Reduced resolution for faster processing
- Optimized detection parameters
- Efficient JPEG encoding
- Background threading for non-blocking operations

### Frontend Optimizations
- Polling-based updates for real-time data
- Canvas-based overlay rendering
- Responsive design for various screen sizes
- Efficient state management

## 🎯 Use Cases

### Security Applications
- **Airport Security** - Identify known criminals and track suspicious individuals
- **Government Buildings** - Monitor access and classify visitors
- **Military Bases** - Track soldier vitals and detect intruders
- **Public Events** - Crowd monitoring and threat detection

### Healthcare Applications
- **Patient Monitoring** - Track vital signs and alert for emergencies
- **Access Control** - Restrict areas based on personnel classification
- **Emergency Response** - Quick identification of medical personnel

## 🔮 Future Enhancements

### Planned Features
- **Database Integration** - Persistent storage for face data
- **Multi-camera Support** - Network-wide surveillance
- **Advanced Analytics** - Behavioral analysis and pattern recognition
- **Mobile App** - Dedicated mobile application
- **Cloud Deployment** - Scalable cloud infrastructure

### Technical Improvements
- **Deep Learning Models** - Enhanced face recognition accuracy
- **Real-time Streaming** - WebRTC for low-latency video
- **Edge Computing** - Distributed processing capabilities
- **IoT Integration** - Sensor network connectivity

## 📄 License
This project is developed for educational and demonstration purposes as part of Nextech 1.0 hackathon.

## 🤝 Contributing
This project was developed by The Unstoppable team for the Nextech 1.0 hackathon. For questions or collaboration, please contact the team members.

## 📞 Contact Information
- **Team**: The Unstoppable
- **Institution**: Regional College of Management, Bhubaneswar
- **Event**: Nextech 1.0 @ NMIET, Bhubaneswar

---

**Jai Hind**

**Built with ❤️ by The Unstoppable Team for Nextech 1.0**
