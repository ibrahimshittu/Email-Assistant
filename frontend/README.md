# Email Assistant Frontend

A modern, beautiful frontend for the Email Assistant application built with Next.js, TypeScript, and shadcn/ui.

## Features

- **Modern UI**: Built with shadcn/ui components and Tailwind CSS for a clean, professional design
- **Email Connection**: Seamlessly connect your email account via Nylas
- **Email Sync**: Sync and index your emails for AI-powered search
- **AI Chat Interface**: Chat with your emails using natural language queries
- **Real-time Streaming**: Streaming responses for faster interaction
- **Responsive Design**: Works beautifully on desktop and mobile devices

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **State Management**: React hooks

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Configure environment variables in `.env.local`:
```env
NEXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm start
```

## Application Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── (app)/             # App routes group
│   │   ├── chat/          # Chat interface
│   │   ├── connect/       # Email connection
│   │   ├── sync/          # Email sync
│   │   └── eval/          # Evaluation page
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/
│   └── ui/                # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── scroll-area.tsx
│       └── avatar.tsx
├── lib/
│   ├── api.ts             # API client
│   ├── sse.ts             # Server-Sent Events handler
│   └── utils.ts           # Utility functions
└── styles/
    └── globals.css        # Global styles and themes

## Pages

### Home (`/`)
- Welcome page with feature overview
- Quick navigation to key features
- Beautiful card-based design

### Connect (`/connect`)
- Email account connection via Nylas
- Account status display
- OAuth flow integration

### Sync (`/sync`)
- Email synchronization interface
- Progress tracking
- Sync results display

### Chat (`/chat`)
- AI-powered chat interface
- Real-time streaming responses
- Source citations with email metadata
- Message history
- Beautiful conversation UI

### Eval (`/eval`)
- Model evaluation and testing
- Performance metrics

## API Integration

The frontend communicates with the backend via:

- **REST API**: For standard operations (connect, sync)
- **Server-Sent Events (SSE)**: For streaming chat responses

### API Endpoints Used

- `GET /auth/nylas/url` - Get OAuth URL
- `GET /auth/me` - Get current account
- `GET /auth/accounts` - List all accounts
- `POST /sync/latest` - Sync latest emails
- `POST /chat` - Send chat message (non-streaming)
- `POST /chat/stream` - Send chat message (streaming)

## Design System

### Colors

The app uses a semantic color system based on HSL variables:

- **Primary**: Blue accent color for CTAs and highlights
- **Secondary**: Gray tones for secondary actions
- **Muted**: Subtle backgrounds and text
- **Destructive**: Error states
- **Border**: Subtle borders throughout the UI

### Components

All UI components follow the shadcn/ui design system for consistency and accessibility:

- Fully accessible with keyboard navigation
- ARIA labels and semantic HTML
- Responsive and mobile-friendly
- Customizable via Tailwind classes

## Features in Detail

### Chat Interface

The chat interface includes:
- Message bubbles with user/assistant distinction
- Avatar icons for visual clarity
- Source citations with expandable email metadata
- Real-time streaming for responsive feel
- Loading states and error handling
- Auto-scrolling to latest message

### Connection Flow

1. User clicks "Connect with Nylas"
2. Redirected to Nylas OAuth page
3. After authorization, redirected back with account info
4. Account details displayed in a beautiful card

### Sync Process

1. User initiates sync
2. Backend fetches latest 200 emails
3. Emails are indexed into vector database
4. Results displayed with message count and chunk count

## Customization

### Theming

Modify `styles/globals.css` to customize the color scheme:

```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96.1%;
  /* ... other variables */
}
```

### Adding Components

To add new shadcn/ui components:

```bash
npx shadcn-ui@latest add [component-name]
```

## Performance

- **Code Splitting**: Automatic route-based code splitting
- **Optimized Images**: Next.js Image optimization
- **Static Generation**: Static pages where possible
- **Tree Shaking**: Unused code eliminated in production

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Build Errors

If you encounter TypeScript errors:
```bash
npm install --save-dev @types/react @types/node
```

### API Connection Issues

Make sure:
1. Backend is running on port 8000
2. CORS is properly configured in backend
3. Environment variables are set correctly

### Styling Issues

If Tailwind classes aren't working:
```bash
npm run dev
```
Restart the dev server to regenerate Tailwind classes.

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new files
3. Ensure all components are accessible
4. Test on multiple screen sizes
5. Keep components small and focused

## License

This project is part of the Email Assistant application.
