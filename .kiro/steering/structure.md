# Project Structure

## Root Directory Layout
```
/
├── backend/                 # Django REST API
├── frontend/               # Next.js React application
├── docs/                   # Project documentation
├── .kiro/                  # Kiro AI assistant configuration
├── .git/                   # Git repository
└── *.py                    # Root-level Python utilities
```

## Backend Structure (Django)
```
backend/
├── api/                    # Main Django app
│   ├── migrations/         # Database migrations
│   ├── models.py          # Data models (Cliente, Animal, Serviço, etc.)
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API ViewSets
│   ├── urls.py            # API URL routing
│   └── admin.py           # Django admin configuration
├── petshop_project/       # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py/asgi.py    # WSGI/ASGI configuration
├── db.sqlite3             # SQLite database file
└── manage.py              # Django management script
```

## Frontend Structure (Next.js)
```
frontend/
├── app/                   # Next.js App Router pages
├── components/            # Reusable UI components
├── contexts/              # React contexts
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions and API clients
├── services/              # API service functions
├── src/                   # Additional source files
├── styles/                # Global styles and CSS
├── types/                 # TypeScript type definitions
├── public/                # Static assets
├── config/                # Configuration files
├── package.json           # Dependencies and scripts
├── next.config.mjs        # Next.js configuration
├── tailwind.config.ts     # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

## Key Conventions

### Backend (Django)
- **Models**: Follow Django naming conventions (PascalCase classes)
- **API Endpoints**: RESTful structure at `/api/[resource]/`
- **ViewSets**: Use DRF ViewSets for consistent CRUD operations
- **Serializers**: One serializer per model, handle validation
- **URLs**: Nested under `/api/` prefix

### Frontend (Next.js)
- **Components**: PascalCase naming, organized by feature/type
- **Pages**: Use Next.js App Router in `/app` directory
- **Styling**: Tailwind CSS classes with shadcn/ui components
- **State**: React hooks and contexts for state management
- **API Calls**: Centralized in `/services` or `/lib` directories
- **Types**: TypeScript interfaces in `/types` directory

### File Naming
- **Backend**: snake_case for Python files
- **Frontend**: camelCase for JS/TS, PascalCase for components
- **Configuration**: Follow framework conventions

### Documentation
- **README files**: In both frontend and docs directories
- **API Documentation**: Inline comments in Django views/serializers
- **Component Documentation**: JSDoc comments for complex components

## Development Workflow
1. Backend changes: Modify models → create migrations → update serializers/views
2. Frontend changes: Update components → test API integration → verify responsiveness
3. Database changes: Always create Django migrations, never edit db.sqlite3 directly