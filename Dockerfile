# --- Stage 1: Build the React Frontend ---
FROM node:18-alpine AS build

WORKDIR /app

# Copy frontend package management files
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY frontend/ ./

# Build the production version of the React app
RUN npm run build

# --- Stage 2: Build the Flask Backend ---
FROM python:3.10-slim

WORKDIR /app

# Copy the backend requirements first
COPY backend/requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory
COPY ./backend .

# Copy the built frontend from the 'build' stage
COPY --from=build /app/build ./static

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application using a production-ready server (Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]