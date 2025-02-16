# Use Python base image
FROM python:3.13

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["python", "cmd/OrderProcessing.py"]
