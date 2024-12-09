# Use a base Python image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all .py files from the current directory and subdirectories into the container
COPY ./*.py .
COPY ./testing/*.py ./testing/
COPY ./testing/groupAnagrams/* ./testing/groupAnagrams/

# Install any dependencies (if required)
# Uncomment the lines below if you have a requirements.txt file
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# Command to run when the container starts
CMD ["python", "node_server.py"]
