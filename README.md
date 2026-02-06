# Budget Zero

A personal finance tracker with automatic transaction categorization.

## Features

- **Account Management**: Track checking, savings, credit cards, and investment accounts
- **Transaction Import**: Upload CSV or OFX files from your bank
- **Auto-Categorization**: Automatically categorize transactions based on keywords and patterns
- **Custom Rules**: Create your own categorization rules for recurring merchants
- **Dashboard**: Visualize spending by category and track income vs expenses over time
- **Category Management**: Create custom categories and subcategories

## Tech Stack

**Backend:**
- FastAPI (Python async web framework)
- SQLAlchemy 2.0 (async ORM)
- PostgreSQL (database)
- Alembic (migrations)
- JWT authentication

**Frontend:**
- React 18 + Vite
- TanStack Query (data fetching)
- Recharts (visualizations)
- Tailwind CSS (styling)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/juniormint88/budget-zero.git
   cd budget-zero
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit .env to set a secure SECRET_KEY
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API docs: http://localhost:8000/docs

### Local Development

#### Backend

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start PostgreSQL (via Docker):
   ```bash
   docker-compose up -d db
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

### Running Tests

```bash
cd backend
pytest
```

## Supported Banks

The CSV parser auto-detects format based on headers. Tested with:

- Chase (checking, savings, credit cards)
- Capital One
- Discover
- Synovus
- Associated Credit Union
- Any bank with standard CSV exports (Date, Description, Amount columns)

OFX/QFX files from any institution are also supported.

## Auto-Categorization

Transactions are automatically categorized using:

1. **User-defined rules** (highest priority) - Custom patterns you create
2. **Built-in patterns** - Common merchants and keywords:
   - Subscriptions: Netflix, Spotify, etc.
   - Groceries: Kroger, Walmart, etc.
   - Dining: DoorDash, Starbucks, etc.
   - And more...

Uncategorized transactions can be manually assigned, and the app will remember your choices for future imports.

## API Documentation

When the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
budget-zero/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Environment configuration
│   │   ├── database.py       # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   └── schemas/          # Pydantic models
│   ├── tests/                # pytest tests
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   └── hooks/            # Custom hooks
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | (change in production!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `1440` (24 hours) |
| `ENVIRONMENT` | `development` or `production` | `development` |

## License

MIT
