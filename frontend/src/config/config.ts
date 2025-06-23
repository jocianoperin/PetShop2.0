export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  appName: 'PetShop',
  defaultTheme: 'light', // 'light' | 'dark' | 'system'
  enableAnalytics: process.env.NODE_ENV === 'production',
} as const;
