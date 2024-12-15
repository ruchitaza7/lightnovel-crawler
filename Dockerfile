# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies from the requirements file and gunicorn
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the entire application code to the container
COPY . .


# Run both gunicorn for the web app and the lncrawl bot using telegram
CMD ["python3 pytest.py"]
