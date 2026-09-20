# Python version
FROM python:3.11-slim

# working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .

# Copy your Python code into the container
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Command to run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]