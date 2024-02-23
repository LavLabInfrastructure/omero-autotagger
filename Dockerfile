# Use the official Python 3 image.
FROM python:3.9-slim

# Create a non-root user.
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
RUN apt update && apt install build-essential
# Set the working directory.
WORKDIR /workspace

# Copy the requirements file.
COPY requirements.txt /workspace/

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-root user.
USER $USERNAME
