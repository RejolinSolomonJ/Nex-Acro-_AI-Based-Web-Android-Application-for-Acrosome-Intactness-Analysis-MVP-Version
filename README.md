# NexAcro: AI-Based Acrosome Intactness Analysis System

![NexAcro Banner](https://img.shields.io/badge/Status-Development-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688?style=for-the-badge&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb)

NexAcro is a state-of-the-art AI-powered platform designed for laboratory professionals and researchers to automate the analysis of acrosome intactness in microscopic sperm images. Using deep learning (CNN), NexAcro provides fast, objective, and accurate classification, significantly reducing the time required for manual visual assessment.

---

##  Key Features

- **AI-Powered Classification**: Utilizes a Convolutional Neural Network (CNN) trained on thousands of microscopic images to distinguish between "Intact" and "Damaged" acrosomes.
- **Batch Processing**: Upload and analyze multiple microscope images simultaneously.
- **Interactive Analytics**: Comprehensive dashboard showing trends, historical data, and success rates.
- **Automated PDF Reporting**: Generate professional, clinical-grade reports with patient details, image grids, and circular intactness graphs.
- **PWA & Mobile Optimized**: Built as a Progressive Web App (PWA) with specific optimizations for Android WebView and a responsive web interface.
- **Secure Access**: JWT-based authentication for secure data management.
- **Local & Cloud Deployment**: Configured for seamless deployment on Render, Vercel, and Docker environments.

---

##  Tech Stack

### Frontend
- **Framework**: [React 19](https://reactjs.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Charts**: [Recharts](https://recharts.org/)
- **PWA**: `vite-plugin-pwa` for offline capabilities and app-like experience.

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database**: [MongoDB](https://www.mongodb.com/) (ODM: PyMongo/Motor)
- **AI/ML**: CNN-based classification (PyTorch/TensorFlow)
- **Report Generation**: ReportLab / Custom PDF Service
- **Environment**: Docker Ready

---

##  Project Structure

```text
├── backend/                # FastAPI Application
│   ├── app/                # Core Logic (Routes, Models, Services)
│   ├── ml_models/          # Trained CNN weights and logic
│   ├── uploads/            # Temporary image storage
│   ├── reports/            # Generated PDF storage
│   └── Dockerfile          # Container configuration
├── frontend/               # React Application (Vite)
│   ├── src/                # Components, Pages, Assets
│   └── public/             # Static icons and manifest
├── render.yaml             # Blueprint for Render.com deployment
└── README.md               # You are here
```

---

##  Getting Started

### Prerequisites
- Node.js (>= 20.19.0)
- Python (>= 3.10)
- MongoDB Atlas account or local instance

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure `.env` file with your `MONGODB_URL` and `SECRET_KEY`.
5. Start the server:
   ```bash
   python run.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure `.env` with `VITE_API_URL`.
4. Run in development mode:
   ```bash
   npm run dev
   ```

---

## 🌐 Deployment

### Render.com
This repository includes a `render.yaml` blueprint. Simply connect your GitHub repository to Render and use the "Blueprint" feature to deploy both the API and the Frontend automatically.

### Vercel
The frontend is optimized for Vercel deployment using the `vercel.json` configuration provided.

Deployed Link : https://www.nexacro.in/

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contact & Support

**Developed by**: Lin's Infotech Company Limited
**Contributed by**: Rejolin Solomon J | Veera Vaishnavi K
**Project Purpose**: MVP Version for Acrosome Intactness Analysis
