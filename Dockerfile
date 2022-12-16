# build stage
FROM python:3.11.1-slim AS builder

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# copy files
COPY . .

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__ && pdm install --prod --no-lock --no-editable


# run stage
FROM python:3.11.1-slim

# retrieve packages from build stage
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.11/lib /project/pkgs

# set command/entrypoint, adapt to fit your needs
CMD ["python", "bot.py"]