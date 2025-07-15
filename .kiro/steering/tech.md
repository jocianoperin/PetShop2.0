# Technology Stack

## Backend
- **Framework**: Django 5.2.3 with Django REST Framework 3.16.0
- **Database**: SQLite (development), PostgreSQL-ready for production
- **Python**: 3.11+
- **Key Libraries**:
  - django-cors-headers 4.7.0 (CORS handling)
  - Pillow 11.2.1 (image processing)

## Frontend
- **Framework**: Next.js 15.2.4 with React 18.2.0
- **Styling**: Tailwind CSS with shadcn/ui components
- **UI Components**: Radix UI primitives (@radix-ui/*)
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **Charts**: Recharts
- **Build Tool**: Next.js built-in bundler

## Development Tools
- **Package Managers**: 
  - Backend: pip (Python packages)
  - Frontend: pnpm (preferred), npm, or yarn
- **Linting**: ESLint (disabled during builds)
- **TypeScript**: Enabled with build error ignoring for rapid development

## Common Commands

### Backend (Django)
```bash
# Navigate to backend directory
cd backend

# Install dependencies (with virtual environment)
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:8000

# Run on specific port
python manage.py runserver 8000
```

### Frontend (Next.js)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install
# or: npm install

# Start development server
pnpm dev
# or: npm run dev

# Build for production
pnpm build
# or: npm run build

# Start production server
pnpm start
# or: npm run start
```

## Default Ports & URLs
- **Frontend**: http://localhost:3000 (Next.js default)
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin

## Admin Credentials
- Username: admin
- Password: admin123