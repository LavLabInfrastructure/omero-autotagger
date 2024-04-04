# use our custom docker image based on the official python/python image
FROM ghcr.io/lavlabinfrastructure/lavlab-omeropy-container

RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode
# Set the working directory.
WORKDIR /workspace

# Copy the requirements file.
COPY requirements.txt /workspace/

# Install dependencies.
RUN /opt/omero-venv/bin/pip3 install --no-cache-dir -r requirements.txt
RUN . /opt/omero-venv/bin/activate

# Switch to the non-root user.
USER vscode
