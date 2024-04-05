ARG OMEROPY_VERSION=latest
FROM ghcr.io/lavlabinfrastructure/lavlab-omeropy-container:$OMEROPY_VERSION

RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode

WORKDIR /app
COPY . /app/
RUN chown -R vscode /app

FROM base AS hatch
RUN pip3 install hatch
ENV HATCH_ENV=default
ENTRYPOINT ["hatch", "run"]

FROM base AS dev
RUN pip3 install hatch 
RUN hatch build
RUN pip3 install $(find requirements -name 'requirement*.txt' -exec echo -n '-r {} ' \;)
USER vscode

FROM base AS prod
COPY --from=dev /app/dist/*.whl /tmp
RUN pip3 install /tmp/*.whl
USER vscode
