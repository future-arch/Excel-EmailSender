# Git Branching Strategy for SmartEmailSender

This document outlines the git branching strategy for developing both desktop and web versions of SmartEmailSender.

## 🌳 Branch Structure

```
main
├── develop                    # Main development branch
│   ├── web-version           # Web version development
│   │   ├── feature/web-backend    # Backend API development
│   │   ├── feature/web-frontend   # Frontend UI development
│   │   ├── feature/web-auth       # Web authentication
│   │   └── feature/web-deploy     # Web deployment
│   ├── desktop-features      # Desktop version new features
│   │   ├── feature/ui-improvements
│   │   ├── feature/performance
│   │   └── feature/integrations
│   └── hotfix/               # Critical bug fixes
└── release/                  # Release preparation branches
    ├── release/v1.1.0
    └── release/web-v1.0.0
```

## 🎯 Branch Purposes

### 📦 **main**
- **Purpose**: Production-ready code
- **Protection**: Protected branch, requires PR reviews
- **Deploys**: Stable releases only
- **Content**: Desktop version (current)

### 🔧 **develop** 
- **Purpose**: Integration branch for all development
- **Merges from**: Feature branches, web-version
- **Merges to**: main (via release branches)
- **Content**: Latest development features

### 🌐 **web-version**
- **Purpose**: Web version development integration
- **Based on**: develop branch
- **Content**: Web-specific architecture and features
- **Merge to**: develop when stable

### ⚡ **Feature Branches**

#### **feature/web-backend**
- FastAPI/Flask backend development
- Microsoft Graph API integration
- Database management
- API endpoints

#### **feature/web-frontend** 
- React/Vue.js frontend development
- Web UI components
- Responsive design
- User experience

#### **feature/web-auth**
- Web-based OAuth2 authentication
- Session management
- Security implementation

#### **feature/web-deploy**
- Docker containerization
- Cloud deployment (Azure/AWS)
- CI/CD pipelines

## 🔄 Workflow Process

### 1. **Desktop Development**
```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/new-desktop-feature

# Development work...
git add .
git commit -m "Add new desktop feature"

# Create PR to develop
git push origin feature/new-desktop-feature
```

### 2. **Web Development**
```bash
# Start from web-version branch
git checkout web-version
git pull origin web-version
git checkout -b feature/web-new-feature

# Development work...
git add .
git commit -m "Add web feature"

# Create PR to web-version
git push origin feature/web-new-feature
```

### 3. **Release Process**
```bash
# Create release branch from develop
git checkout develop
git checkout -b release/v1.1.0

# Final testing and bug fixes
git add .
git commit -m "Release v1.1.0 preparation"

# Merge to main
git checkout main
git merge release/v1.1.0
git tag v1.1.0

# Merge back to develop
git checkout develop
git merge release/v1.1.0
```

## 🎨 Web Version Architecture Plan

### 🏗️ **Backend (FastAPI/Flask)**
```
web-backend/
├── app/
│   ├── api/                  # API endpoints
│   │   ├── auth.py          # Authentication
│   │   ├── emails.py        # Email operations
│   │   ├── groups.py        # Microsoft 365 groups
│   │   └── files.py         # File uploads
│   ├── core/                # Core functionality
│   │   ├── graph_client.py  # Microsoft Graph integration
│   │   ├── email_processor.py # Email processing
│   │   └── template_engine.py # Template rendering
│   ├── models/              # Data models
│   ├── database/            # Database operations
│   └── utils/               # Utilities
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 🎨 **Frontend (React/Vue.js)**
```
web-frontend/
├── public/
├── src/
│   ├── components/          # Reusable components
│   │   ├── EmailEditor/     # HTML email editor
│   │   ├── DataTable/       # Excel data display
│   │   ├── AttachmentManager/ # File management
│   │   └── GroupSelector/   # M365 group selection
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── EmailComposer.tsx # Email composition
│   │   └── Analytics.tsx    # Send analytics
│   ├── services/            # API services
│   ├── store/               # State management
│   └── utils/               # Utilities
├── package.json
└── Dockerfile
```

## 🚀 Development Commands

### **Switch to Web Development**
```bash
# Start web backend development
git checkout feature/web-backend

# Start web frontend development  
git checkout feature/web-frontend

# Work on main web version
git checkout web-version
```

### **Sync with Latest Changes**
```bash
# Update web-version with develop changes
git checkout web-version
git merge develop

# Update feature branch with web-version changes
git checkout feature/web-backend
git merge web-version
```

### **Push Branches to GitHub**
```bash
# Push all branches
git push origin develop
git push origin web-version
git push origin feature/web-backend
git push origin feature/web-frontend
```

## 📋 Best Practices

### ✅ **Do**
- Create feature branches for each new feature
- Write descriptive commit messages
- Keep branches up to date with parent branches
- Use pull requests for code review
- Test thoroughly before merging

### ❌ **Don't**
- Commit directly to main or develop
- Create long-lived feature branches
- Merge without code review
- Push broken code to shared branches

## 🎯 Web Version Goals

### **Phase 1: Backend API**
- [ ] Microsoft Graph API integration
- [ ] Authentication system
- [ ] Email sending endpoints
- [ ] File upload handling
- [ ] Database setup

### **Phase 2: Frontend UI**
- [ ] React/Vue.js setup
- [ ] Email composer interface
- [ ] Data import/management
- [ ] Real-time progress tracking
- [ ] Responsive design

### **Phase 3: Integration**
- [ ] Frontend-backend integration
- [ ] Testing and debugging
- [ ] Performance optimization
- [ ] Security hardening

### **Phase 4: Deployment**
- [ ] Docker containerization
- [ ] Cloud deployment setup
- [ ] CI/CD pipeline
- [ ] Production monitoring

This branching strategy provides a clear, organized approach to developing both desktop and web versions simultaneously while maintaining code quality and project organization.