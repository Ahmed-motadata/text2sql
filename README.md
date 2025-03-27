# Text2SQL: Multi-Agent SQL Query Generation

A modern web application that converts natural language queries into SQL statements using a multi-agent approach. Built with Next.js, Node.js, and PostgreSQL.

## Features

- Natural language to SQL query conversion
- Real-time database connection management
- Interactive SQL query execution
- Schema visualization
- Paginated results for large datasets
- Modern, responsive UI
- Connection status monitoring

## Tech Stack

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- React Context API
- Axios

### Backend
- Node.js
- Express.js
- PostgreSQL
- Redis (for large result caching)
- Knex.js (SQL query builder)

## Prerequisites

- Node.js (v18 or higher)
- PostgreSQL
- Redis (optional, for large result caching)
- npm or yarn

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text2sql.git
cd text2sql
```

2. Install dependencies:
```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
npm install
```

3. Set up environment variables:

Frontend (.env.local):
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api
```

Backend (.env):
```env
PORT=5001
NODE_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
REDIS_URL=redis://localhost:6379
```

4. Create the database:
```bash
psql -U postgres -c "CREATE DATABASE your_database;"
```

## Development

1. Start the backend server:
```bash
cd backend
npm run dev
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

## Project Structure

```
text2sql/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/            # Next.js app router pages
│   │   ├── components/     # Reusable React components
│   │   └── contexts/       # React context providers
│   └── public/             # Static assets
├── backend/                 # Node.js backend application
│   ├── config/            # Configuration files
│   ├── controllers/       # Route controllers
│   ├── services/         # Business logic
│   ├── utils/           # Utility functions
│   └── routes/          # API routes
└── README.md
```

## API Endpoints

- `GET /api/db/test-connection` - Test database connection
- `GET /api/db/tables` - Get all tables
- `GET /api/db/schema-info` - Get database schema information
- `POST /api/db/execute` - Execute SQL query
- `GET /api/db/query-results/:queryId/:page` - Get paginated query results
- `POST /api/db/disconnect` - Disconnect from database

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Next.js team for the amazing framework
- PostgreSQL team for the robust database
- All contributors and maintainers of the open-source libraries used in this project