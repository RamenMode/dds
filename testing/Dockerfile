# Use a base Python image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all .py files from the current directory and subdirectories into the container
COPY ./*.py .

# Command to run when the container starts
CMD ["python", "node_server.py"]
