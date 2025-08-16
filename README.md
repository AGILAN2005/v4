# Apollo Assist 🏥  

An Intelligent, Multilingual Voice Agent for Seamless Patient Care, powered by LiveKit and Google Gemini.  

---

<div align="center">
    <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Waving%20Hand.png" alt="Waving Hand" width="70" height="70" />
</div>

<p align="center">
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python" alt="Python Version">
    <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">
    <a href="https://livekit.io/"><img src="https://img.shields.io/badge/Framework-LiveKit%20Agents-orange?style=for-the-badge&logo=livekit" alt="LiveKit Agents"></a>
    <a href="https://deepmind.google/technologies/gemini/"><img src="https://img.shields.io/badge/LLM-Google%20Gemini-purple?style=for-the-badge&logo=google" alt="Google Gemini"></a>
    <img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=for-the-badge&logo=github" alt="Contributions Welcome">
</p>

<p align="center">
  <i>This repository contains the source code for <b>Apollo Assist</b>, a real-time, conversational AI designed to automate and enhance patient-receptionist interactions at hospitals. It understands Tamil and English, manages appointments, recommends doctors, and sends SMS notifications.</i>
</p>

<div align="center">
  <img src="https://github.com/user-attachments/assets/e20f0190-67c0-42c2-808b-5975d0b98583" alt="Demo GIF of Apollo Assist in Action" width="800"/>
</div>

---

## ✨ Features  

- **🗣️ Multilingual Conversational AI:** Communicates in **English**, **Tamil**, and **Hindi**.  
- **🗓️ Appointment Lifecycle Management:** Booking, rescheduling, and cancellation.  
- **👨‍⚕️ Doctor Recommendation:** Intelligent suggestions based on specialization and history.  
- **📞 Real-Time Voice Interaction:** Ultra-low latency via **LiveKit Agents**.  
- **🧠 Powered by Google Gemini:** Cutting-edge LLM for NLU/NLG.  
- **🔔 SMS Notifications:** Instant reminders via **Twilio**.  
- **⚡ High Performance:** Optimized with **Redis cache** and rate limiter.  
- **💾 Flexible Data Storage:** Supports **CSV**, **PostgreSQL**, **Google Sheets**.  
- **📊 Analytics:** Tracks booking patterns, cancellations, and doctor popularity.  

---

## 🛠️ Technology Stack  

| Category | Technology |
| --- | --- |
| **AI & Agent** | ![LiveKit](https://img.shields.io/badge/LiveKit-Agents-orange?style=for-the-badge&logo=livekit) ![Gemini](https://img.shields.io/badge/Google-Gemini-purple?style=for-the-badge&logo=google) |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white) |
| **Database/Cache** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white) |
| **Notifications** | ![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white) |
| **DevOps** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white) |

---

## 🏗️ Architecture Overview  

Apollo Assist operates as a **real-time agent** that processes audio streams, understands intent, and interacts with scheduling systems.  

```mermaid
graph TD
    A[User (Patient)] -- Voice Call --> B(LiveKit);
    B -- Audio Stream --> C{Apollo Assist Agent};
    C -- NLU/NLG --> D(Google Gemini LLM);
    C -- Tools --> E(Function Tools);

    subgraph "Backend Services"
        E -- Calls --> F(Appointment Scheduler);
        F -- Manages --> G[Data Source (CSV/Postgres)];
        F -- Caches --> H(Redis Cache);
        F -- Triggers --> I(Twilio SMS);
    end

    style C fill:#ffb3ff,stroke:#333,stroke-width:2px
    style D fill:#d1e0ff,stroke:#333,stroke-width:2px
```

---

## 🚀 Getting Started  

### Prerequisites  

- Python 3.9+  
- Redis Server  
- LiveKit Project  
- API Keys (**Google, LiveKit, Twilio**)  

### Installation  

```sh
git clone https://github.com/your-username/apollo-assist.git
cd apollo-assist
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables  

Copy `.env.example` → `.env`  

```sh
cp .env.example .env
```

Update your credentials inside `.env`. Example:  

```env
LIVEKIT_URL="wss://your-project.livekit.cloud"
LIVEKIT_API_KEY="your_api_key"
LIVEKIT_API_SECRET="your_api_secret"
GOOGLE_API_KEY="your_google_cloud_api_key"
```

---

## ▶️ Running the Agent  

### 1. Console Mode (local testing)  

```sh
python agent.py console
```

### 2. LiveKit Mode (deployment)  

```sh
python agent.py dev
```

---

## 📁 Project Structure  

> Click filenames to open source code in GitHub directly.  

```
.
├── [.env](./.env)                  # Environment variables
├── [agent.py](./agent.py)          # Entrypoint for LiveKit agent
├── [config.py](./config.py)        # Pydantic settings
├── [instructions.py](./instructions.py)  # Core LLM instructions
├── [requirements.txt](./requirements.txt) # Dependencies
├── [scheduler.py](./scheduler.py)  # Appointment logic
├── [seed.py](./seed.py)            # Initial doctor data seeder
├── data/                           # CSV data files
│   ├── [doctors.csv](./data/doctors.csv)
│   └── ...
└── utils/                          # Utility modules
    ├── [cache_manager.py](./utils/cache_manager.py)
    ├── [csv_manager.py](./utils/csv_manager.py)
    ├── [date_parser.py](./utils/date_parser.py)
    ├── [exceptions.py](./utils/exceptions.py)
    ├── [language_support.py](./utils/language_support.py)
    ├── [notifications.py](./utils/notifications.py)
    └── ...
```

---

## 🤝 Contributing  

We ❤️ contributions!  

1. Fork it  
2. Create branch: `git checkout -b feature/awesome`  
3. Commit: `git commit -m 'Add awesome feature'`  
4. Push: `git push origin feature/awesome`  
5. Open a PR 🎉  

---


---
