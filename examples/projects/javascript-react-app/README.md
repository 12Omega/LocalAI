# JavaScript React App Example Project

This example demonstrates using the Local AI Development Environment to build a React application with TypeScript from scratch.

## Project Structure

```
javascript-react-app/
├── src/
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── UserProfile.tsx
│   ├── hooks/
│   │   └── useApi.ts
│   ├── utils/
│   │   └── helpers.ts
│   ├── App.tsx
│   └── index.tsx
├── public/
│   └── index.html
├── tests/
│   ├── components/
│   │   └── UserProfile.test.tsx
│   └── utils/
│       └── helpers.test.ts
├── package.json
├── tsconfig.json
└── README.md
```

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run development server:**
   ```bash
   npm start
   ```

3. **Run tests:**
   ```bash
   npm test
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## Example Tasks for the AI

### Task 1: Create a new component

```
Create a UserProfile React component that displays user information including:
- Avatar image
- Username
- Email
- Bio text
- Member since date

The component should:
- Use TypeScript with proper type definitions
- Accept user data as props
- Be responsive (mobile-friendly)
- Include unit tests with React Testing Library
```

### Task 2: Add custom hook

```
Create a custom React hook called useApi that:
- Accepts a URL endpoint
- Fetches data with loading and error states
- Returns { data, loading, error, refetch }
- Handles HTTP errors gracefully
- Includes TypeScript types
- Includes unit tests
```

### Task 3: Implement form validation

```
Create a UserRegistrationForm component with validation for:
- Email (valid format)
- Password (min 8 chars, 1 uppercase, 1 number, 1 special char)
- Username (3-20 chars, alphanumeric)
- Age (18+)

Display validation errors inline as user types.
Include tests for validation logic.
```

### Task 4: Add state management

```
Refactor the app to use React Context for global state management:
- Create AuthContext for user authentication state
- Create ThemeContext for light/dark theme toggle
- Update components to consume context
- Include tests for context providers
```

### Task 5: Add API integration

```
Integrate with a REST API:
- Create an API client service using fetch
- Add error handling and retry logic
- Implement authentication with JWT tokens
- Add request/response interceptors
- Include tests using MSW (Mock Service Worker)
```

### Task 6: Debug performance issue

```
The UserList component is re-rendering too frequently causing performance issues.
Debug and optimize using:
- React.memo for component memoization
- useMemo for expensive computations
- useCallback for event handlers
Verify improvements with React Profiler.
```

### Task 7: Add accessibility

```
Improve accessibility of the UserProfile component:
- Add proper ARIA labels
- Ensure keyboard navigation works
- Add focus management
- Test with screen reader
- Ensure color contrast meets WCAG AA standards
```

## What the AI Will Do

1. **Analyze Context**: The AI will identify this as a React/TypeScript project, understand the component structure, and recognize conventions.

2. **Generate Components**: The AI will create React functional components with proper TypeScript types, following React best practices.

3. **Write Tests**: The AI will create test files using React Testing Library and Jest, testing component rendering, user interactions, and edge cases.

4. **Follow Conventions**: The AI will match the project's coding style including:
   - Functional components with hooks
   - TypeScript interfaces for props
   - Named exports for components
   - Descriptive test names

5. **Verify Changes**: The AI will run `npm test` to ensure all tests pass and `npm run build` to verify the code compiles.

## Expected Behavior

- **Code Style**: ESLint and Prettier rules followed
- **TypeScript**: Strict type checking, no `any` types
- **Components**: Functional components with hooks (no class components)
- **Testing**: React Testing Library with user-centric test approach
- **Accessibility**: WCAG compliance considered
- **Performance**: Memoization where appropriate

## Technology Stack

- **React**: 18.x
- **TypeScript**: 4.x
- **Testing**: Jest + React Testing Library
- **Build**: Webpack / Create React App / Vite
- **Linting**: ESLint + Prettier
- **State Management**: React Context / Redux Toolkit (optional)

## Common Patterns

The AI will recognize and follow these React patterns:

**Component Structure**:
```typescript
import React from 'react';

interface UserProfileProps {
  user: User;
  onUpdate?: (user: User) => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ user, onUpdate }) => {
  return (
    <div className="user-profile">
      {/* Component content */}
    </div>
  );
};
```

**Custom Hook**:
```typescript
import { useState, useEffect } from 'react';

export const useApi = <T,>(url: string) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Fetch logic
  }, [url]);

  return { data, loading, error };
};
```

**Test Structure**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { UserProfile } from './UserProfile';

describe('UserProfile', () => {
  it('renders user information correctly', () => {
    const user = { name: 'John Doe', email: 'john@example.com' };
    render(<UserProfile user={user} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
```

## Tips for Success

1. **Be Specific**: Provide clear requirements with examples
2. **Mention Technologies**: Specify if you want Context, Redux, styled-components, etc.
3. **Request Tests**: Explicitly ask for tests to ensure they're included
4. **Indicate Conventions**: Mention if you prefer certain patterns or libraries
5. **Ask for Accessibility**: Request WCAG compliance for accessible components
