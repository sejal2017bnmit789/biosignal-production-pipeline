# 1. Use an official lightweight Python runtime as a parent image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /project

# 3. Set system environment variables to optimize Python inside Docker
# Prevents Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr (crucial for real-time Cloud Run logging)
ENV PYTHONUNBUFFERED=1

# 4. Install system dependencies required for compiling certain wheels if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy just the requirements file first to leverage Docker's caching mechanism
COPY requirements.txt .

# 6. Install the production dependencies locked in your requirements file
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy the application logic files into the container
COPY ./app ./app

# 8. Inform Docker that the container listens on port 8080 at runtime
EXPOSE 8080

# 9. Command to launch the FastAPI server using Uvicorn
# Note: GCP Cloud Run requires your container to bind to 0.0.0.0 and listen to port 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
