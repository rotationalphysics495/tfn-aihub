#!/bin/bash
#
# BMAD Epic Execute - Automated Story Execution with Context Isolation
#
# Usage: ./epic-execute.sh <epic-id> [options]
#
# Options:
#   --dry-run       Show what would be executed without running
#   --skip-review   Skip code review phase (not recommended)
#   --no-commit     Stage changes but don't commit
#   --parallel      Run independent stories in parallel (experimental)
#   --verbose       Show detailed output
#   --start-from ID Start from a specific story (e.g., 31-2)
#   --skip-done     Skip stories with Status: Done
#

set -e

# =============================================================================
# Pipeline Protection
# =============================================================================
# CRITICAL: This script must NOT be piped to head/tail/etc as it will cause
# premature termination when the pipe closes. Detect and warn.

if [ ! -t 1 ] && [ -z "$EPIC_EXECUTE_ALLOW_PIPE" ]; then
    # stdout is not a terminal (being piped)
    echo "WARNING: epic-execute.sh output is being piped." >&2
    echo "This can cause premature script termination if piped to head/tail/etc." >&2
    echo "To suppress this warning, set EPIC_EXECUTE_ALLOW_PIPE=1" >&2
    echo "" >&2
    # Don't exit - just warn, in case it's being piped to tee or a log file
fi

# Ignore SIGPIPE to prevent script death when pipe closes
trap '' PIPE 2>/dev/null || true

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BMAD_DIR="$PROJECT_ROOT/_bmad"

STORIES_DIR="$PROJECT_ROOT/_bmad-output/implementation-artifacts"
SPRINT_ARTIFACTS_DIR="$PROJECT_ROOT/_bmad-output/implementation-artifacts"
SPRINTS_DIR="$PROJECT_ROOT/_bmad-output/sprints"
EPICS_DIR="$PROJECT_ROOT/_bmad-output/planning-artifacts"
UAT_DIR="$PROJECT_ROOT/_bmad-output/uat"
ISSUES_DIR="$PROJECT_ROOT/_bmad-output/issues"
SPRINT_STATUS_FILE="$SPRINT_ARTIFACTS_DIR/sprint-status.yaml"
STORY_FILES_DIR="$PROJECT_ROOT/_bmad-output/stories"

LOG_FILE="/tmp/bmad-epic-execute-$$.log"

# Retry and degradation settings
MAX_RETRIES=2
CONSECUTIVE_FAILURE_THRESHOLD=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    echo -e "${BLUE}[BMAD]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1" >> "$LOG_FILE"
}

# =============================================================================
# Story Completion Verification Functions
# =============================================================================

# Check if story is marked as done in the story file
check_story_file_done() {
    local story_id="$1"
    local story_file="$STORY_FILES_DIR/${story_id}.md"

    if [ -f "$story_file" ]; then
        if grep -qi "^Status:.*Done" "$story_file" 2>/dev/null; then
            return 0  # Done
        fi
    fi
    return 1  # Not done
}

# Check if story is marked as done in sprint-status.yaml
check_sprint_status_done() {
    local story_id="$1"

    if [ -f "$SPRINT_STATUS_FILE" ]; then
        if grep -q "^[[:space:]]*${story_id}:.*done" "$SPRINT_STATUS_FILE" 2>/dev/null; then
            return 0  # Done
        fi
    fi
    return 1  # Not done
}

# Check both sources for done status
is_story_done() {
    local story_id="$1"

    if check_story_file_done "$story_id" && check_sprint_status_done "$story_id"; then
        return 0  # Both confirm done
    fi
    return 1  # Not confirmed done in both
}

# Update sprint-status.yaml to mark story as done
update_sprint_status() {
    local story_id="$1"
    local new_status="$2"

    if [ -f "$SPRINT_STATUS_FILE" ]; then
        # Use sed to update the status
        sed -i.bak "s/^\([[:space:]]*${story_id}:\).*/\1 ${new_status}/" "$SPRINT_STATUS_FILE"
        rm -f "${SPRINT_STATUS_FILE}.bak"
        log "Updated sprint-status.yaml: $story_id -> $new_status"
    fi
}

# Verify story completion after dev+review cycle
verify_story_completion() {
    local story_id="$1"
    local story_file="$2"

    # Check story file status
    if ! grep -qi "^Status:.*Done" "$story_file" 2>/dev/null; then
        log_warn "Story file not marked as Done: $story_id"
        return 1
    fi

    # Update sprint-status.yaml
    update_sprint_status "$story_id" "done"

    # Verify both are now in sync
    if is_story_done "$story_id"; then
        log_success "Story completion verified: $story_id"
        return 0
    else
        log_warn "Story completion verification failed: $story_id"
        return 1
    fi
}

# =============================================================================
# Issue File Creation
# =============================================================================

create_issue_file() {
    local issue_type="$1"
    local story_id="$2"
    local message="$3"
    local details="$4"

    mkdir -p "$ISSUES_DIR"

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local issue_file="$ISSUES_DIR/issue-${timestamp}-${story_id}.md"

    cat > "$issue_file" << EOF
# Epic Chain Issue Report

**Generated**: $(date '+%Y-%m-%d %H:%M:%S')
**Epic**: $EPIC_ID
**Story**: $story_id
**Issue Type**: $issue_type

## Summary

$message

## Details

$details

## Context

- Log File: $LOG_FILE
- Metrics File: $METRICS_FILE
- Sprint Status: $SPRINT_STATUS_FILE

## Recommended Actions

EOF

    case "$issue_type" in
        "degradation")
            cat >> "$issue_file" << EOF
1. Review the log file for error patterns
2. Check if there are environmental issues (API limits, memory, etc.)
3. Consider running stories individually to isolate the problem
4. Resume with: ./scripts/epic-execute.sh $EPIC_ID --start-from $story_id --skip-done
EOF
            ;;
        "consecutive_failures")
            cat >> "$issue_file" << EOF
1. Multiple consecutive stories have failed
2. This may indicate a systemic issue with the codebase or test environment
3. Review failed stories and their error messages
4. Fix underlying issues before resuming
5. Resume with: ./scripts/epic-execute.sh $EPIC_ID --start-from $story_id --skip-done
EOF
            ;;
        "verification_failed")
            cat >> "$issue_file" << EOF
1. Story completed but verification failed
2. Check if story file status was updated correctly
3. Manually verify sprint-status.yaml is in sync
4. Resume with: ./scripts/epic-execute.sh $EPIC_ID --start-from $story_id --skip-done
EOF
            ;;
        *)
            cat >> "$issue_file" << EOF
1. Review the error details above
2. Check the log file for more context
3. Resume with: ./scripts/epic-execute.sh $EPIC_ID --start-from $story_id --skip-done
EOF
            ;;
    esac

    log_error "Issue file created: $issue_file"
    echo "$issue_file"
}

# =============================================================================
# Metrics Functions
# =============================================================================

METRICS_DIR=""
METRICS_FILE=""

init_metrics() {
    METRICS_DIR="$SPRINT_ARTIFACTS_DIR/metrics"
    METRICS_FILE="$METRICS_DIR/epic-${EPIC_ID}-metrics.yaml"
    mkdir -p "$METRICS_DIR"

    local start_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$METRICS_FILE" << EOF
epic_id: "$EPIC_ID"
execution:
  start_time: "$start_time"
  end_time: ""
  duration_seconds: 0
stories:
  total: 0
  completed: 0
  failed: 0
  skipped: 0
validation:
  gate_executed: false
  gate_status: "PENDING"
  fix_attempts: 0
issues: []
EOF

    log "Metrics initialized: $METRICS_FILE"
}

update_story_metrics() {
    local status="$1"  # completed|failed|skipped

    if [ -z "$METRICS_FILE" ] || [ ! -f "$METRICS_FILE" ]; then
        return 0
    fi

    # Check if yq is available for YAML manipulation
    if command -v yq >/dev/null 2>&1; then
        case "$status" in
            completed) yq -i '.stories.completed += 1' "$METRICS_FILE" ;;
            failed)    yq -i '.stories.failed += 1' "$METRICS_FILE" ;;
            skipped)   yq -i '.stories.skipped += 1' "$METRICS_FILE" ;;
        esac
    else
        # Fallback: log warning (metrics will be finalized at end)
        if [ "$VERBOSE" = true ]; then
            log_warn "yq not found - metrics update deferred"
        fi
    fi
    return 0
}

add_metrics_issue() {
    local story_id="$1"
    local issue_type="$2"
    local message="$3"

    if [ -z "$METRICS_FILE" ] || [ ! -f "$METRICS_FILE" ]; then
        return
    fi

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    if command -v yq >/dev/null 2>&1; then
        yq -i ".issues += [{\"story\": \"$story_id\", \"type\": \"$issue_type\", \"message\": \"$message\", \"timestamp\": \"$timestamp\"}]" "$METRICS_FILE"
    fi
}

finalize_metrics() {
    local total_stories="$1"
    local completed="$2"
    local failed="$3"
    local skipped="$4"
    local duration="$5"

    if [ -z "$METRICS_FILE" ] || [ ! -f "$METRICS_FILE" ]; then
        return
    fi

    local end_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    if command -v yq >/dev/null 2>&1; then
        yq -i ".execution.end_time = \"$end_time\"" "$METRICS_FILE"
        yq -i ".execution.duration_seconds = $duration" "$METRICS_FILE"
        yq -i ".stories.total = $total_stories" "$METRICS_FILE"
        yq -i ".stories.completed = $completed" "$METRICS_FILE"
        yq -i ".stories.failed = $failed" "$METRICS_FILE"
        yq -i ".stories.skipped = $skipped" "$METRICS_FILE"
    else
        # Fallback: rewrite the file with final values
        cat > "$METRICS_FILE" << EOF
epic_id: "$EPIC_ID"
execution:
  start_time: "$EPIC_START_TIME"
  end_time: "$end_time"
  duration_seconds: $duration
stories:
  total: $total_stories
  completed: $completed
  failed: $failed
  skipped: $skipped
validation:
  gate_executed: false
  gate_status: "PENDING"
  fix_attempts: 0
issues: []
EOF
    fi

    log "Metrics finalized: $METRICS_FILE"
}

# =============================================================================
# Argument Parsing
# =============================================================================

EPIC_ID=""
DRY_RUN=false
SKIP_REVIEW=false
NO_COMMIT=false
PARALLEL=false
VERBOSE=false
START_FROM=""
SKIP_DONE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-review)
            SKIP_REVIEW=true
            shift
            ;;
        --no-commit)
            NO_COMMIT=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --start-from)
            START_FROM="$2"
            shift 2
            ;;
        --skip-done)
            SKIP_DONE=true
            shift
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            EPIC_ID="$1"
            shift
            ;;
    esac
done

if [ -z "$EPIC_ID" ]; then
    echo "Usage: $0 <epic-id> [options]"
    echo ""
    echo "Options:"
    echo "  --dry-run       Show what would be executed"
    echo "  --skip-review   Skip code review phase"
    echo "  --no-commit     Don't commit after stories"
    echo "  --parallel      Parallel execution (experimental)"
    echo "  --verbose       Detailed output"
    echo "  --start-from ID Start from a specific story (e.g., 31-2)"
    echo "  --skip-done     Skip stories with Status: Done"
    echo ""
    echo "WARNING: Do NOT pipe output to head/tail/etc - this kills the script!"
    echo "  BAD:  ./epic-execute.sh 8 | head -100"
    echo "  GOOD: ./epic-execute.sh 8"
    echo "  GOOD: ./epic-execute.sh 8 2>&1 | tee epic.log"
    exit 1
fi

# =============================================================================
# Setup
# =============================================================================

log "Starting epic execution for: $EPIC_ID"
log "Project root: $PROJECT_ROOT"

# Ensure directories exist
mkdir -p "$UAT_DIR"
mkdir -p "$SPRINTS_DIR"

# Initialize metrics collection
EPIC_START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EPIC_START_SECONDS=$(date +%s)
init_metrics

# Find epic file (supports both epic-39-*.md and epic-039-*.md formats)
EPIC_FILE=""
# Pad epic ID with leading zero for 3-digit format (e.g., 40 -> 040)
EPIC_ID_PADDED=$(printf "%03d" "$EPIC_ID" 2>/dev/null || echo "$EPIC_ID")
for pattern in "epic-${EPIC_ID}.md" "epic-${EPIC_ID}-"*.md "epic-${EPIC_ID_PADDED}-"*.md "epic-0${EPIC_ID}-"*.md "${EPIC_ID}.md"; do
    found=$(find "$EPICS_DIR" -name "$pattern" 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        EPIC_FILE="$found"
        break
    fi
done

if [ -z "$EPIC_FILE" ] || [ ! -f "$EPIC_FILE" ]; then
    log_error "Epic file not found for: $EPIC_ID"
    log_error "Searched in: $EPICS_DIR"
    exit 1
fi

log "Found epic file: $EPIC_FILE"

# =============================================================================
# Discover Stories
# =============================================================================

log "Discovering stories..."

# Search multiple locations for story files
STORY_LOCATIONS=("$STORIES_DIR" "$SPRINT_ARTIFACTS_DIR" "$SPRINTS_DIR")
STORIES=()

for search_dir in "${STORY_LOCATIONS[@]}"; do
    if [ ! -d "$search_dir" ]; then
        continue
    fi
    
    # Method 1: Stories that reference this epic in content
    while IFS= read -r -d '' file; do
        if [[ ! " ${STORIES[*]} " =~ " ${file} " ]]; then
            STORIES+=("$file")
        fi
    done < <(grep -l -Z "Epic.*:.*${EPIC_ID}\|epic-${EPIC_ID}\|Epic.*${EPIC_ID}" "$search_dir"/*.md 2>/dev/null || true)
    
    # Method 2: {EpicNumber}-{StoryNumber}-{description}.md (e.g., 1-1-user-registration.md)
    while IFS= read -r -d '' file; do
        if [[ ! " ${STORIES[*]} " =~ " ${file} " ]]; then
            STORIES+=("$file")
        fi
    done < <(find "$search_dir" -name "${EPIC_ID}-*-*.md" -print0 2>/dev/null || true)
    
    # Method 3: story-{epic}.{seq}-*.md (BMAD standard)
    while IFS= read -r -d '' file; do
        if [[ ! " ${STORIES[*]} " =~ " ${file} " ]]; then
            STORIES+=("$file")
        fi
    done < <(find "$search_dir" -name "story-${EPIC_ID}.*-*.md" -print0 2>/dev/null || true)
    
    # Method 4: story-{epic}-*.md (BMAD alternate)
    while IFS= read -r -d '' file; do
        if [[ ! " ${STORIES[*]} " =~ " ${file} " ]]; then
            STORIES+=("$file")
        fi
    done < <(find "$search_dir" -name "story-${EPIC_ID}-*.md" -print0 2>/dev/null || true)
done

if [ ${#STORIES[@]} -eq 0 ]; then
    log_error "No stories found for epic: $EPIC_ID"
    log_error "Searched in: ${STORY_LOCATIONS[*]}"
    log_error "Looking for:"
    log_error "  - Files containing 'Epic: $EPIC_ID'"
    log_error "  - Files named: ${EPIC_ID}-*-*.md (e.g., ${EPIC_ID}-1-description.md)"
    log_error "  - Files named: story-${EPIC_ID}.*.md or story-${EPIC_ID}-*.md"
    exit 1
fi

log "Found ${#STORIES[@]} stories"

# Sort stories for consistent execution order
IFS=$'\n' STORIES=($(sort -V <<<"${STORIES[*]}")); unset IFS

# Show which directories stories came from
if [ "$VERBOSE" = true ]; then
    for story in "${STORIES[@]}"; do
        echo "  - $story"
    done
fi

# =============================================================================
# Execution Functions
# =============================================================================

execute_dev_phase() {
    local story_file="$1"
    local story_id=$(basename "$story_file" .md)

    log ">>> DEV PHASE: $story_id (using BMAD dev-story workflow)"

    # Build BMAD workflow invocation prompt
    # This invokes the actual dev-story workflow which:
    # - Loads project-context.md for coding standards
    # - Uses red-green-refactor TDD cycle
    # - Tracks sprint-status.yaml
    # - Validates definition-of-done
    local dev_prompt="Execute the BMAD dev-story workflow for story: $story_file

CRITICAL INSTRUCTIONS:
1. Load the workflow configuration from: _bmad/bmm/workflows/4-implementation/dev-story/workflow.yaml
2. Load the workflow instructions from: _bmad/bmm/workflows/4-implementation/dev-story/instructions.xml
3. Execute the workflow steps exactly as specified in instructions.xml
4. The story file path is: $story_file
5. Run in YOLO mode - do NOT ask for user confirmation, proceed autonomously
6. Complete ALL tasks and subtasks in the story
7. Run tests and ensure they pass
8. Update the story file Status to 'review' when complete
9. Stage all changes with: git add -A

When the workflow completes successfully, output exactly: IMPLEMENTATION COMPLETE: $story_id
If blocked or failed, output: IMPLEMENTATION BLOCKED: $story_id - [reason]"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would execute BMAD dev-story workflow for $story_id"
        return 0
    fi

    # Execute in isolated context
    # Note: timeout command not available on macOS by default, so we run without hard timeout
    # The BMAD workflow has its own completion logic
    local result
    result=$(claude --dangerously-skip-permissions -p "$dev_prompt" 2>&1) || true

    echo "$result" >> "$LOG_FILE"

    if echo "$result" | grep -q "IMPLEMENTATION COMPLETE"; then
        log_success "Dev phase complete: $story_id"
        return 0
    elif echo "$result" | grep -q "IMPLEMENTATION BLOCKED"; then
        log_error "Dev phase blocked: $story_id"
        echo "$result" | grep "IMPLEMENTATION BLOCKED"
        return 1
    else
        log_error "Dev phase did not complete cleanly: $story_id"
        return 1
    fi
}

execute_review_phase() {
    local story_file="$1"
    local story_id=$(basename "$story_file" .md)

    log ">>> REVIEW PHASE: $story_id (using BMAD code-review workflow, fresh context)"

    # Build BMAD code-review workflow invocation prompt
    # This invokes the adversarial code-review workflow which:
    # - Validates git diff vs story file claims
    # - Verifies each AC is actually implemented
    # - Audits task completion (marked [x] but not done = CRITICAL)
    # - Finds 3-10 issues minimum
    # - Auto-fixes HIGH and MEDIUM issues
    local review_prompt="Execute the BMAD code-review workflow for story: $story_file

CRITICAL INSTRUCTIONS:
1. Load the workflow configuration from: _bmad/bmm/workflows/4-implementation/code-review/workflow.yaml
2. Load the workflow instructions from: _bmad/bmm/workflows/4-implementation/code-review/instructions.xml
3. Execute the workflow steps exactly as specified in instructions.xml
4. The story file path is: $story_file
5. Run in YOLO mode - automatically fix issues (choose option 1 when prompted)
6. Be ADVERSARIAL - find 3-10 specific issues minimum
7. Verify git diff matches story File List claims
8. Check that tasks marked [x] are actually implemented
9. Fix all HIGH severity issues and MEDIUM if total > 5
10. Update story Status to 'done' if review passes
11. Stage all changes with: git add -A

When the review passes, output exactly: REVIEW PASSED: $story_id
If fixes were applied, output: REVIEW PASSED WITH FIXES: $story_id - Fixed N issues
If review fails (unfixable issues), output: REVIEW FAILED: $story_id - [reason]"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would execute BMAD code-review workflow for $story_id"
        return 0
    fi

    # Execute in isolated context
    # Note: timeout command not available on macOS by default, so we run without hard timeout
    # The BMAD workflow has its own completion logic
    local result
    result=$(claude --dangerously-skip-permissions -p "$review_prompt" 2>&1) || true

    echo "$result" >> "$LOG_FILE"

    if echo "$result" | grep -q "REVIEW PASSED"; then
        log_success "Review passed: $story_id"
        return 0
    elif echo "$result" | grep -q "REVIEW FAILED"; then
        log_error "Review failed: $story_id"
        echo "$result" | grep "REVIEW FAILED"
        return 1
    else
        log_warn "Review did not complete cleanly: $story_id"
        return 1
    fi
}

commit_story() {
    local story_id="$1"
    
    if [ "$NO_COMMIT" = true ]; then
        log "Skipping commit (--no-commit)"
        return 0
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would commit: feat(epic-$EPIC_ID): complete $story_id"
        return 0
    fi
    
    git add -A
    git commit -m "feat(epic-$EPIC_ID): complete $story_id" || {
        log_warn "Nothing to commit for $story_id"
    }
    
    log_success "Committed: $story_id"
}

generate_uat() {
    log ">>> GENERATING UAT DOCUMENT (fresh context)"
    
    local epic_contents=$(cat "$EPIC_FILE")
    local all_stories=""
    
    for story_file in "${STORIES[@]}"; do
        local story_id=$(basename "$story_file" .md)
        all_stories+="
<story id=\"$story_id\">
$(cat "$story_file")
</story>
"
    done
    
    local uat_prompt="You are a QA Specialist creating a User Acceptance Testing document.

## Your Task

Generate a UAT document for Epic: $EPIC_ID

## Epic Definition

<epic>
$epic_contents
</epic>

## Completed Stories

$all_stories

## Requirements

Create a UAT document for NON-TECHNICAL users with:

1. **Overview**: What was built (plain language)
2. **Prerequisites**: Test environment, accounts, setup
3. **Test Scenarios**: Step-by-step instructions with expected results
4. **Success Criteria**: Checklist of what must work
5. **Sign-off Section**: For human approval

Write for someone who can use the software but doesn't know how it's built.

## Output

Save to: $UAT_DIR/epic-${EPIC_ID}-uat.md

When complete, output: UAT GENERATED: $UAT_DIR/epic-${EPIC_ID}-uat.md"

    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would generate UAT document"
        return 0
    fi
    
    local result
    result=$(claude --dangerously-skip-permissions -p "$uat_prompt" 2>&1) || true
    
    echo "$result" >> "$LOG_FILE"
    
    if echo "$result" | grep -q "UAT GENERATED"; then
        log_success "UAT document generated"
    else
        log_warn "UAT generation may not have completed cleanly"
    fi
    
    # Commit UAT document
    if [ "$NO_COMMIT" = false ]; then
        git add "$UAT_DIR/epic-${EPIC_ID}-uat.md" 2>/dev/null || true
        git commit -m "docs(epic-$EPIC_ID): add UAT document" 2>/dev/null || true
    fi
}

# =============================================================================
# Main Execution Loop
# =============================================================================

log "=========================================="
log "Starting execution of ${#STORIES[@]} stories"
log "=========================================="

# Ensure issues directory exists
mkdir -p "$ISSUES_DIR"

COMPLETED=0
FAILED=0
SKIPPED=0
CONSECUTIVE_FAILURES=0
START_TIME=$(date +%s)
STARTED=false

for story_file in "${STORIES[@]}"; do
    story_id=$(basename "$story_file" .md)

    # --start-from: Skip stories until we reach the specified one
    if [ -n "$START_FROM" ] && [ "$STARTED" = false ]; then
        if [[ "$story_id" == *"$START_FROM"* ]]; then
            STARTED=true
        else
            log_warn "Skipping $story_id (waiting for $START_FROM)"
            ((SKIPPED++))
            update_story_metrics "skipped"
            continue
        fi
    fi

    # --skip-done: Check BOTH story file AND sprint-status.yaml
    if [ "$SKIP_DONE" = true ]; then
        story_file_done=false
        sprint_status_done=false

        # Check story file
        if grep -qi "^Status:.*Done" "$story_file" 2>/dev/null; then
            story_file_done=true
        fi

        # Check sprint-status.yaml
        if [ -f "$SPRINT_STATUS_FILE" ] && grep -q "^[[:space:]]*${story_id}:.*done" "$SPRINT_STATUS_FILE" 2>/dev/null; then
            sprint_status_done=true
        fi

        # Skip if EITHER source says done (to be safe)
        if [ "$story_file_done" = true ] || [ "$sprint_status_done" = true ]; then
            log_warn "Skipping $story_id (already done - file:$story_file_done, status:$sprint_status_done)"
            ((SKIPPED++))
            update_story_metrics "skipped"
            continue
        fi
    fi

    echo ""
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Story: $story_id"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Track retry attempts for this story
    STORY_SUCCESS=false
    RETRY_COUNT=0

    while [ "$STORY_SUCCESS" = false ] && [ $RETRY_COUNT -le $MAX_RETRIES ]; do
        if [ $RETRY_COUNT -gt 0 ]; then
            log_warn "Retry attempt $RETRY_COUNT/$MAX_RETRIES for $story_id"
        fi

        DEV_SUCCESS=false
        REVIEW_SUCCESS=false

        # DEV PHASE (Context 1)
        if execute_dev_phase "$story_file"; then
            DEV_SUCCESS=true
            log_success "Dev phase complete: $story_id"
        else
            log_error "Dev phase failed for $story_id (attempt $((RETRY_COUNT + 1)))"
            ((RETRY_COUNT++))
            continue
        fi

        # REVIEW PHASE (Context 2 - Fresh)
        if [ "$SKIP_REVIEW" = false ]; then
            if execute_review_phase "$story_file"; then
                REVIEW_SUCCESS=true
            else
                log_error "Review phase failed for $story_id (attempt $((RETRY_COUNT + 1)))"
                ((RETRY_COUNT++))
                continue
            fi
        else
            REVIEW_SUCCESS=true
        fi

        # If we got here, both phases succeeded
        if [ "$DEV_SUCCESS" = true ] && [ "$REVIEW_SUCCESS" = true ]; then
            STORY_SUCCESS=true
        fi
    done

    # Handle story result
    if [ "$STORY_SUCCESS" = true ]; then
        # COMMIT
        commit_story "$story_id"

        # VERIFY completion in both sources
        if ! verify_story_completion "$story_id" "$story_file"; then
            log_warn "Story completion verification failed, but continuing..."
            # Still count as completed since code review passed
        fi

        ((COMPLETED++))
        CONSECUTIVE_FAILURES=0  # Reset on success
        update_story_metrics "completed"
        log_success "Story complete: $story_id ($COMPLETED/${#STORIES[@]})"
    else
        # Story failed after all retries
        ((FAILED++))
        ((CONSECUTIVE_FAILURES++))
        update_story_metrics "failed"
        add_metrics_issue "$story_id" "story_failed" "Failed after $MAX_RETRIES retries"

        log_error "Story failed after $MAX_RETRIES retries: $story_id"

        # Check for consecutive failure threshold
        if [ $CONSECUTIVE_FAILURES -ge $CONSECUTIVE_FAILURE_THRESHOLD ]; then
            log_error "DEGRADATION DETECTED: $CONSECUTIVE_FAILURES consecutive failures"

            # Create issue file
            issue_details="Consecutive failures: $CONSECUTIVE_FAILURES
Failed stories in sequence ending with: $story_id
Total completed before stopping: $COMPLETED
Total failed: $FAILED

This indicates potential systemic issues with:
- The codebase or test environment
- API rate limits or service availability
- Memory or resource constraints"

            create_issue_file "consecutive_failures" "$story_id" \
                "Epic chain stopped due to $CONSECUTIVE_FAILURES consecutive story failures" \
                "$issue_details"

            log_error "Epic chain halted due to degradation. Check issue file for details."

            # Finalize metrics before exit
            END_TIME=$(date +%s)
            DURATION=$((END_TIME - START_TIME))
            finalize_metrics "${#STORIES[@]}" "$COMPLETED" "$FAILED" "$SKIPPED" "$DURATION"

            exit 2  # Exit code 2 indicates degradation stop
        fi
    fi
done

# =============================================================================
# UAT Generation (Context 3 - Fresh)
# =============================================================================

echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "UAT Document Generation"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

generate_uat

# =============================================================================
# Summary
# =============================================================================

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Finalize metrics with final counts
finalize_metrics "${#STORIES[@]}" "$COMPLETED" "$FAILED" "$SKIPPED" "$DURATION"

echo ""
log "=========================================="
log "EPIC EXECUTION COMPLETE"
log "=========================================="
echo ""
echo "  Epic:       $EPIC_ID"
echo "  Duration:   ${DURATION}s"
echo "  Stories:    ${#STORIES[@]}"
echo "  Skipped:    $SKIPPED"
echo "  Completed:  $COMPLETED"
echo "  Failed:     $FAILED"
echo ""
echo "  Deliverables:"
echo "    - Stories:  $STORIES_DIR/"
echo "    - UAT:      $UAT_DIR/epic-${EPIC_ID}-uat.md"
echo "    - Metrics:  $METRICS_FILE"
echo "    - Log:      $LOG_FILE"
echo ""

if [ $FAILED -gt 0 ]; then
    log_warn "$FAILED stories failed - check log for details"
    exit 1
fi

log_success "All stories completed successfully"
echo ""
echo "Next step: Run UAT document with a human tester"
echo ""
