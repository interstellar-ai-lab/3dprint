# 3D Generation Frontend

A modern React frontend for the Multi-Agent 3D Generation application.

## Features

- 🎨 **Modern UI/UX**: Beautiful gradient design with responsive layout
- 🚀 **Real-time Updates**: Live polling of generation progress using React Query
- 🖼️ **Image Display**: Interactive image grid with modal view
- 📊 **Progress Tracking**: Visual progress bar and status indicators
- 📱 **Mobile Responsive**: Works on desktop and mobile devices
- ⚡ **TypeScript**: Full type safety and better developer experience
- 🎯 **State Management**: Zustand for local state, React Query for server state

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **React Query** for server state management
- **Zustand** for local state management
- **Axios** for API communication
- **Heroicons** for icons

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:8000](http://localhost:8000) to view it in the browser.

**Note**: Make sure your Flask backend is running on http://localhost:8001

### Building for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # React components
│   ├── GenerationForm.tsx
│   ├── StatusDisplay.tsx
│   ├── ImageGrid.tsx
│   └── EvaluationResults.tsx
├── stores/             # Zustand stores
│   └── generationStore.ts
├── api/                # API layer
│   └── generationApi.ts
├── App.tsx             # Main app component
└── index.tsx           # Entry point
```

## API Integration

The frontend communicates with the Flask backend through the following endpoints:

- `POST /api/generate` - Start a new generation session
- `GET /api/status/{session_id}` - Get session status
- `GET /api/image/{session_id}/{iteration}` - Get iteration image
- `GET /api/sessions` - List all sessions
- `GET /api/health` - Health check

## Development

### Adding New Components

1. Create a new component in `src/components/`
2. Use TypeScript interfaces for props
3. Follow the existing styling patterns with Tailwind CSS
4. Add proper error handling and loading states

### Styling

The app uses Tailwind CSS with custom configurations:
- Custom color palette in `tailwind.config.js`
- Responsive design utilities
- Custom animations and transitions

### State Management

- **Zustand**: For local UI state (form data, current session)
- **React Query**: For server state (API calls, caching, real-time updates)

## Deployment

The frontend can be deployed to various platforms:

- **Vercel**: Connect your GitHub repository
- **Netlify**: Drag and drop the build folder
- **AWS S3**: Upload the build folder to S3
- **Docker**: Use the provided Dockerfile

## Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:8001
```

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for all new features
3. Include proper error handling
4. Test on both desktop and mobile devices
