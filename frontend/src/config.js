// API configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? ''  // For production/Vercel, use relative URLs to the same domain
  : 'http://127.0.0.1:5000';  // For development, use the Flask backend

export { API_BASE_URL };