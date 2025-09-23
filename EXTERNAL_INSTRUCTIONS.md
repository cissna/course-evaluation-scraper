# External Setup Instructions for JHU Course Evaluation Analyzer

This document provides the necessary steps to set up the backend infrastructure for the JHU Course Evaluation Analyzer, including the PostgreSQL database and the Vercel serverless deployment.

## 1. Supabase Database Setup

We will use Supabase to create a free PostgreSQL database.

1.  **Create a Supabase Account**: Go to [supabase.com](https://supabase.com) and sign up for a free account.
2.  **Create a New Project**:
    *   Once you are logged in, click on "New project".
    *   Give your project a name and generate a secure password for the database. **Save this password securely**, as you will need it for the connection string.
    *   Choose a region that is geographically close to you.
    *   Click "Create new project".
3.  **Get the Database Connection String**:
    *   After the project is created, navigate to the "Project Settings" (the gear icon in the left sidebar).
    *   Click on "Database".
    *   Under "Connection string", select the "URI" tab.
    *   Copy the connection string. It will look something like this:
        ```
        postgresql://postgres:[YOUR-PASSWORD]@[AWS-REGION].pooler.supabase.com:5432/postgres
        ```
    *   Replace `[YOUR-PASSWORD]` with the password you created in step 2.

## 2. Local Environment Setup

To run the backend locally and to perform the initial database setup, you need to set up an environment variable.

1.  **Create a `.env` file**: In the root directory of the project, create a new file named `.env`.
2.  **Set the `DATABASE_URL`**: Add the following line to the `.env` file, replacing the placeholder with your actual Supabase connection string:
    ```
    DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[AWS-REGION].pooler.supabase.com:5432/postgres
    ```

## 3. Database Initialization and Data Migration

You need to run two scripts to set up the database schema and migrate the existing data from the JSON files.

1.  **Install Dependencies**: Make sure you have all the required Python packages installed. The backend dependencies are in `backend/requirements.txt` and the script dependencies are in `requirements.txt`. You should install both:
    ```bash
    pip install -r requirements.txt
    pip install -r backend/requirements.txt
    ```
2.  **Run the Database Setup Script**: This will create the necessary tables in your Supabase database.
    ```bash
    python3 db_setup.py
    ```
    You should see a message "Database schema created successfully."
3.  **Run the Data Migration Script**: This will load the data from `data.json` and `metadata.json` into your new database.
    ```bash
    python3 migrate_data.py
    ```
    You should see messages indicating that the migration is complete.

## 4. Deploying to Vercel

Now you can deploy the backend to Vercel as a serverless application.

1.  **Install the Vercel CLI**: If you haven't already, install the Vercel CLI globally:
    ```bash
    npm install -g vercel
    ```
2.  **Log in to Vercel**:
    ```bash
    vercel login
    ```
3.  **Deploy the Application**: Run the following command from the root of the project:
    ```bash
    vercel --prod
    ```
    Vercel will guide you through the process of creating a new project.
4.  **Set Environment Variables in Vercel**:
    *   Go to your project's dashboard on the Vercel website.
    *   Navigate to the "Settings" tab and then "Environment Variables".
    *   Add a new environment variable with the key `DATABASE_URL` and the value of your Supabase connection string.
    *   Make sure the variable is available to all environments (Production, Preview, and Development).
5.  **Redeploy**: After setting the environment variable, you may need to trigger a new deployment for the changes to take effect. You can do this from the Vercel dashboard.

Your backend should now be live and connected to your Supabase database. You will need to update the frontend to point to your new Vercel API endpoint.
