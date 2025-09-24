# Use official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LOCAL_DATA=/app/local_data
ENV GITHUB_REPO_URL="https://github.com/akshit7093/speech-translator-using-vosk.git"
ENV GITHUB_BRANCH="main"
ENV LOG_FILE="/app/git_changes.log"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create entrypoint script
RUN echo '#!/bin/bash\nset -e\n\nlog_changes() {\n    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")\n    local status_output=$(cd "$LOCAL_DATA" && git status --porcelain)\n    \n    if [ -n "$status_output" ]; then\n        echo "[$timestamp] Detected changes after pull:" >> "$LOG_FILE"\n        \n        while IFS= read -r line; do\n            status_code="${line:0:2}"\n            file_path="${line:3}"\n            \n            case "$status_code" in\n                "??") change_type="New file" ;;\n                "A ") change_type="Added" ;;\n                "M ") change_type="Modified" ;;\n                "D ") change_type="Deleted" ;;\n                "R ") change_type="Renamed" ;;\n                *) change_type="Changed" ;;\n            esac\n            \n            echo "  $change_type: $file_path" >> "$LOG_FILE"\n        done <<< "$status_output"\n        \n        echo "" >> "$LOG_FILE"\n        echo "[$(date)] Changes logged to $LOG_FILE"\n    else\n        echo "[$(date)] No changes detected after pull"\n    fi\n}\n\n# Initialize Git repository if needed\nif [ ! -d "$LOCAL_DATA/.git" ]; then\n    echo "[$(date)] Initializing Git repository in $LOCAL_DATA"\n    mkdir -p "$LOCAL_DATA"\n    cd "$LOCAL_DATA"\n    git init\n    git remote add origin "$GITHUB_REPO_URL"\n    \n    # Try to fetch and checkout the branch\n    if git fetch origin "$GITHUB_BRANCH" 2>/dev/null; then\n        git checkout -b "$GITHUB_BRANCH" origin/"$GITHUB_BRANCH"\n    else\n        # If branch doesn\'t exist yet, create it\n        git commit --allow-empty -m "Initial commit"\n        git fetch origin "$GITHUB_BRANCH"\n        git checkout -b "$GITHUB_BRANCH" origin/"$GITHUB_BRANCH"\n    fi\nfi\n\n# Pull latest changes\necho "[$(date)] Pulling latest changes from $GITHUB_REPO_URL ($GITHUB_BRANCH)..." \ncd "$LOCAL_DATA"\n\nif git fetch origin "$GITHUB_BRANCH"; then\n    if git reset --hard origin/"$GITHUB_BRANCH"; then\n        echo "[$(date)] Successfully synchronized with GitHub repository"\n        log_changes\n    else\n        echo "[$(date)] Failed to reset to remote branch" >&2\n    fi\nelse\n    echo "[$(date)] Failed to fetch from GitHub" >&2\nfi\n\necho "[$(date)] Starting application..."\nexec "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (will be overwritten by Git pull, but needed for first run)
COPY . .

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["python", "app.py"]

# Expose port
EXPOSE 5000