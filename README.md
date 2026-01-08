# TALOS Backend

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   - Copy `.env` to a new file (if needed) or fill in the details in `.env`.
   - Ensure Firebase credentials and Razorpay keys are set.

## Running the App

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Project Structure

- `app/models`: Pydantic models (Schemas)
- `app/routes`: API endpoints
- `app/services`: External services (Firebase, Razorpay, Email)
- `app/main.py`: Application entry point
