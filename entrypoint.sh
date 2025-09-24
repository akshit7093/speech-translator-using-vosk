# Create the file with proper Unix line endings
$entrypointContent = @'
#!/bin/bash
set -e

# Configuration
REPO_DIR="/app/local_data"
GITHUB_REPO_URL="https://github.com/akshit7093/speech-translator-using-vosk.git"
LOG_FILE="/app/git_changes.log"
GITHUB_BRANCH="main"

# Function to log changes
log_changes() {
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    local status_output=$(cd "$REPO_DIR" && git status --porcelain)
    
    if [ -n "$status_output" ]; then
        echo "[$timestamp] Detected changes after pull:" >> "$LOG_FILE"
        
        # Convert status codes to human-readable format
        while IFS= read -r line; do
            status_code="${line:0:2}"
            file_path="${line:3}"
            
            case "$status_code" in
                "??") change_type="New file" ;;
                "A ") change_type="Added" ;;
                "M ") change_type="Modified" ;;
                "D ") change_type="Deleted" ;;
                "R ") change_type="Renamed" ;;
                *) change_type="Changed" ;;
            esac
            
            echo "  $change_type: $file_path" >> "$LOG_FILE"
        done <<< "$status_output"
        
        echo "" >> "$LOG_FILE"
        echo "[$(date)] Changes logged to $LOG_FILE"
    else
        echo "[$(date)] No changes detected after pull"
    fi
}

# Initialize Git repository if needed
if [ ! -d "$REPO_DIR/.git" ]; then
    echo "[$(date)] Initializing Git repository in $REPO_DIR"
    mkdir -p "$REPO_DIR"
    cd "$REPO_DIR"
    git init
    git remote add origin "$GITHUB_REPO_URL"
    
    # Try to fetch and checkout the branch
    if git fetch origin "$GITHUB_BRANCH" 2>/dev/null; then
        git checkout -b "$GITHUB_BRANCH" origin/"$GITHUB_BRANCH"
    else
        # If branch doesn't exist yet, create it
        git commit --allow-empty -m "Initial commit"
        git fetch origin "$GITHUB_BRANCH"
        git checkout -b "$GITHUB_BRANCH" origin/"$GITHUB_BRANCH"
    fi
fi

# Pull latest changes
echo "[$(date)] Pulling latest changes from $GITHUB_REPO_URL ($GITHUB_BRANCH)..."
cd "$REPO_DIR"

# Fetch and reset to remote branch
if git fetch origin "$GITHUB_BRANCH"; then
    if git reset --hard origin/"$GITHUB_BRANCH"; then
        echo "[$(date)] Successfully synchronized with GitHub repository"
        
        # Check for changes and log them
        log_changes
    else
        echo "[$(date)] Failed to reset to remote branch" >&2
    fi
else
    echo "[$(date)] Failed to fetch from GitHub" >&2
fi

# Execute the main application
echo "[$(date)] Starting application..."
exec "$@"
'@

# Write with UTF8 encoding and Unix line endings
[IO.File]::WriteAllText("entrypoint.sh", $entrypointContent, [System.Text.Encoding]::UTF8)