# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY . /app

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

RUN pip install diffusers
RUN pip install rembg
RUN pip install onnxruntime
RUN pip install google-generativeai
RUN pip install openai

# Default command to run FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
