# Use the official Python 3 image.
FROM ghcr.io/lavlabinfrastructure/lavlab-omeropy-container
# Create a non-root user.
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
# Set the working directory.
WORKDIR /workspace

# Copy the requirements file.
COPY requirements.txt /workspace/

# Install dependencies.
RUN /opt/omero-venv/bin/pip3 install --no-cache-dir -r requirements.txt
RUN . /opt/omero-venv/bin/activate

# Switch to the non-root user.
USER $USERNAME