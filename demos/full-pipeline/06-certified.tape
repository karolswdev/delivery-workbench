Output demos/rendered/segments/06-certified.mp4

Require dw
Set Shell "bash"
Set FontSize 16
Set Width 1280
Set Height 720
Set Theme "Dracula"
Set TypingSpeed 30ms

Hide
Type "source /tmp/dw-ceremony-demo/env.sh && cd tic-tac-toe && RUN=$(jq -r .run_id .tmp/start.json) && clear"
Enter
Show

Type "# The program stopped at certified handoff. It has no authority to commit. The operator does."
Enter
Type `META=$(for f in .git/pmo-programs/runs/$RUN/conductor/artifacts/*/metadata.json; do jq -r 'select(.artifact_kind=="git-diff") | input_filename' $f; done | tail -1)`
Enter
Type "jq '{name, artifact_kind, sha256, bytes}' $META"
Enter
Sleep 3.5s

Hide
Type "clear"
Enter
Show
Type "# Inspect, then accept the exact certified diff into the index."
Enter
Type "git apply --stat $(dirname $META)/content | tail -6"
Enter
Sleep 3.5s
Type "git apply --index $(dirname $META)/content && git status --short | head -8"
Enter
Sleep 3s

Hide
Type "clear"
Enter
Show
Type "# Prove it. The declared regression command, run by the operator's own hands."
Enter
Type `node --test 2>&1 | tail -n 12`
Enter
Wait+Screen@120s /pass [0-9]+/
Sleep 3.5s

Hide
Type "clear"
Enter
Show
Type "# Capture the real run as story evidence."
Enter
Set TypingSpeed 10ms
Type `.githooks/dw evidence capture tic-tac-toe 1 TTT-1-01 -- node --test > /dev/null && git add -A && echo CAPTURED"-ok"`
Enter
Set TypingSpeed 30ms
Wait+Screen@120s /CAPTURED-ok/
Sleep 1.5s

Hide
Type "clear"
Enter
Show
Type "# The guarded finish refuses without evidence. With it, the story flips."
Enter
Set TypingSpeed 10ms
Type `.githooks/dw step tic-tac-toe --json > .tmp/step.json && jq -r '.action.id' .tmp/step.json && eval "$(jq -r '.apply_command | @sh' .tmp/step.json)" > /dev/null`
Enter
Wait+Screen@30s /finish-story/
Hide
Type "clear"
Enter
Show
Type "# One story was the whole phase - the gate insists the phase closes in the same commit."
Enter
Type ".githooks/dw phase close tic-tac-toe 1 --summary 'Delivered by one governed grant: live claude implemented, checks passed, live codex certified, the operator integrated and shipped.'"
Enter
Sleep 2s
Type `git add -A && .githooks/dw step tic-tac-toe --json > .tmp/step.json && eval "$(jq -r '.apply_command | @sh' .tmp/step.json)" > /dev/null && sed -i '' 's/- \[ \]/- [x]/' .tmp/CONTRACT.md`
Enter
Set TypingSpeed 30ms
Sleep 2s
Type "git commit -m 'Complete TTT-1-01: two-player Tic Tac Toe over WebSockets'"
Enter
Wait+Screen@30s /Commit proceeding/
Sleep 2.5s

Hide
Type "clear"
Enter
Show
Type "# History itself re-verifies. No local state needed."
Enter
Type ".githooks/dw verify --all && git log --oneline"
Enter
Wait+Screen@60s /dw verify: ok/
Sleep 5s
