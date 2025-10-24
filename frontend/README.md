# Medical Education Grading System - Frontend Portals

This directory contains two separate Next.js applications for the Medical Education Grading System:

## 📁 Directory Structure

```
frontend/
├── instructor-portal/    # Portal for instructors
└── student-portal/       # Portal for students
```

## 🎯 Portals Overview

### Instructor Portal (Port 3000)
**Purpose**: Manage rubrics and review student submissions

**Features**:
- Dashboard with system overview
- Upload and manage grading rubrics
- View all student submissions
- Review detailed grading results
- View feedback and citations

**Pages**:
- `/` - Dashboard
- `/rubrics` - Rubric management
- `/submissions` - Student submissions
- `/results` - Grading results

### Student Portal (Port 3001)
**Purpose**: Submit presentations and view grades

**Features**:
- Personal dashboard with performance metrics
- Submit case presentations (transcript + optional audio)
- View grades and detailed feedback
- Track progress over time

**Pages**:
- `/` - Dashboard
- `/submit` - Submit presentation
- `/grades` - View grades and feedback

## 🚀 Local Development

### Prerequisites
- Node.js 18+ and npm
- Backend services running (see main README)

### Setup

1. **Install dependencies for both portals**:
```bash
# Instructor Portal
cd frontend/instructor-portal
npm install

# Student Portal
cd frontend/student-portal
npm install
```

2. **Run in development mode**:
```bash
# Terminal 1 - Instructor Portal
cd frontend/instructor-portal
npm run dev
# Runs on http://localhost:3000

# Terminal 2 - Student Portal
cd frontend/student-portal
npm run dev
# Runs on http://localhost:3001
```

3. **Configure API URL** (optional):
Create `.env.local` in each portal directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🐳 Docker Deployment

### Build Docker Images

```bash
# From project root
docker compose build instructor-portal student-portal
```

### Run with Docker Compose

```bash
# Start all services including frontends
docker compose up -d

# Access portals
# Instructor: http://localhost:3000
# Student: http://localhost:3001
```

## 🏗️ Production Build

```bash
# Instructor Portal
cd frontend/instructor-portal
npm run build
npm start

# Student Portal
cd frontend/student-portal
npm run build
npm start
```

## 🎨 Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Build**: Docker multi-stage builds

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |
| `NODE_ENV` | Environment mode | `development` |
| `PORT` | Server port | `3000` (instructor), `3001` (student) |

## 🔗 API Integration

Both portals connect to the backend microservices through the Grading Orchestrator service:

- **Instructor Portal** → `/api/rubrics`, `/api/results`
- **Student Portal** → `/api/grade`, `/api/submissions`

## 📦 Deployment to AWS

The frontends are deployed as static sites on S3 + CloudFront:

1. **Build production bundles**:
```bash
npm run build
```

2. **Deploy to S3**:
```bash
# Automated via Terraform
terraform apply
```

3. **Access via CloudFront**:
- Instructor Portal: `https://instructor.your-domain.com`
- Student Portal: `https://student.your-domain.com`

## 🧪 Testing

```bash
# Lint check
npm run lint

# Type check
npx tsc --noEmit
```

## 📚 Additional Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Main Project README](../README.md)

## 🤝 Contributing

When adding new features:
1. Follow the existing component structure
2. Use TypeScript for type safety
3. Follow Tailwind CSS utility-first approach
4. Test with both development and production builds
5. Ensure responsive design (mobile, tablet, desktop)

## 📄 License

Part of the Medical Education Grading System project.

