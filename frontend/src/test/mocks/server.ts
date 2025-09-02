import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup mock service worker server for API testing
export const server = setupServer(...handlers);
