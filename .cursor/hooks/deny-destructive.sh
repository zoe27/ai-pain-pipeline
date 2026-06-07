#!/usr/bin/env bash
# Block destructive shell commands during Agent runs.
# Only inspect lines that look like executable shell (not heredoc doc bullets).
set -euo pipefail

input=$(cat)
command=$(printf '%s' "$input" | python3 -c "import sys, json; print(json.load(sys.stdin).get('command', ''))")

deny=0
while IFS= read -r line || [[ -n "$line" ]]; do
  trimmed="${line#"${line%%[![:space:]]*}"}"
  case "$trimmed" in
    git\ push*--force*|git\ push\ -f\ *|git\ push\ --force*)
      deny=1
      break
      ;;
    rm\ -rf*|rm\ -fr*)
      deny=1
      break
      ;;
    git\ reset\ --hard*)
      deny=1
      break
      ;;
    git\ clean\ -fdx*)
      deny=1
      break
      ;;
  esac
done <<< "$command"

if [[ "$deny" -eq 1 ]]; then
  printf '%s\n' '{"permission":"deny","user_message":"Blocked: destructive command (project hook). Approve manually if intentional.","agent_message":"Matched deny-destructive hook on an executable line."}'
  exit 0
fi

# No output: defer to permissions.json / Run Mode for allow vs ask.
exit 0
