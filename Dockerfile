# PMO Status Report Automation - container image
#
# Builds an image that can run the full pipeline (Flatten -> Intake ->
# Prioritization -> HTML report -> PPTX report, with optional --interactive
# human-in-the-loop review gates) against a client folder mounted at runtime.
#
# Build:
#   docker build -t rqc-framework .
#
# Run (mount an input folder read-only, and an output folder to collect results):
#   docker run --rm \
#     -e ANTHROPIC_API_KEY=sk-ant-... \
#     -v "%cd%/sample_data/inputs/Fabiani:/data/input:ro" \
#     -v "%cd%/output:/app/output" \
#     rqc-framework --input-dir /data/input --practice PMO
#
# Run with the interactive review gates (needs an attached terminal, -it):
#   docker run --rm -it \
#     -e ANTHROPIC_API_KEY=sk-ant-... \
#     -v "%cd%/sample_data/inputs/Fabiani:/data/input:ro" \
#     -v "%cd%/output:/app/output" \
#     rqc-framework --input-dir /data/input --practice PMO --interactive

FROM python:3.11-slim

# Force UTF-8 everywhere regardless of the container's locale, so the emoji
# in the pipeline's progress output can't crash a print() call the way it did
# on Windows' default console encoding before run_pipeline.py forced it.
ENV PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code and the (required-at-runtime) PPTX brand template. Sample
# data and generated output are intentionally not part of the image - they're
# supplied/collected via volume mounts at `docker run` time (see usage above).
COPY agents/ agents/
COPY scripts/ scripts/
COPY templates/ templates/
COPY run_pipeline.py .

RUN mkdir -p /app/output

ENTRYPOINT ["python", "run_pipeline.py"]
CMD ["--help"]
