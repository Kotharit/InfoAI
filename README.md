# Infographic Studio

AI-powered infographic generator that transforms reports into stunning visual stories.

## Features

- PDF upload or text paste
- AI-powered visual blueprint generation (Gemini)
- Nano Banana Pro image generation
- Customizable settings (layout, creativity, palette, text density, tone)
- Simple auth (admin/contributor roles)
- Dark/light theme toggle

## Tech Stack

- **Frontend**: React, Tailwind CSS
- **Backend**: FastAPI, Python
- **AI**: Google Gemini API (text + image generation)
- **Database**: MongoDB (optional for Vercel)

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### Frontend
```bash
cd frontend
yarn install
yarn start
```

## Vercel Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Import to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key

### 3. Environment Variables (Vercel Dashboard)

Add these in Vercel Project Settings → Environment Variables:

| Name | Value |
|------|-------|
| `GEMINI_API_KEY` | `AIzaSy...` (your key) |

### 4. Build Settings

Vercel should auto-detect settings from `vercel.json`. If not:

- **Framework Preset**: Other
- **Build Command**: `cd frontend && yarn build`
- **Output Directory**: `frontend/build`

## Demo Credentials

- **Admin**: `admin` / `admin123` (unlimited usage)
- **Contributor**: `contributor` / `contrib123` (2 uses)

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/auth/login` - Login
- `GET /api/auth/usage/:username` - Get usage count
- `POST /api/generate` - Generate infographic

## Project Structure

```
├── backend/
│   ├── server.py          # FastAPI app
│   ├── requirements.txt   # Python dependencies
│   └── compiler/
│       └── prompt_compiler.py  # Blueprint to prompt converter
├── frontend/
│   ├── src/
│   │   └── App.js         # React app
│   └── package.json
├── vercel.json            # Vercel configuration
└── README.md
```

## License

MIT
