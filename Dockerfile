ARG OMEROPY_VERSION=latest
FROM ghcr.io/lavlabinfrastructure/lavlab-omeropy-container:$OMEROPY_VERSION as base

RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode

WORKDIR /app
COPY . /app/
RUN chown -R vscode /app

RUN pip3 install hatch
RUN hatch run build

FROM base AS hatch
ENV HATCH_ENV=default
ENTRYPOINT ["hatch", "run"]

FROM base AS prod
RUN pip3 install /app/dist/*.whl
USER vscode

FROM base as dev
ENV PATH ~/.local/bin:$PATH
RUN pip3 install hatch 
RUN find requirements -name 'requirement*.txt' | while read requirement; do \
        pip3 install -r "$requirement"; \
    done
USER vscode
