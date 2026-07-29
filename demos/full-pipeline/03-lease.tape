Output demos/rendered/segments/03-lease.mp4

Require dw
Set Shell "bash"
Set FontSize 16
Set Width 1280
Set Height 720
Set Theme "Dracula"
Set TypingSpeed 30ms

Hide
Type "source /tmp/dw-ceremony-demo/env.sh && cd tic-tac-toe && clear"
Enter
Show

Type "# Reviewed in the browser. The reviewer accepts by advancing the state."
Enter
Type `jq '.state = "reviewed"' .tmp/proposal.json > .tmp/proposal.reviewed.json`
Enter
Sleep 1.5s

Hide
Type "clear"
Enter
Show
Type "# Preview the exact write set. The lease token binds this repo, this stage, this content."
Enter
Type ".githooks/dw setup preview .tmp/proposal.reviewed.json > .tmp/preview.json"
Enter
Type "jq '{proposal_id, expect, writes: (.changes | length)}' .tmp/preview.json"
Enter
Wait+Screen@30s /setup-sha256/
Sleep 4s

Hide
Type "clear"
Enter
Show
Type "# Apply that one lease. This is the first human approval."
Enter
Set TypingSpeed 10ms
Type `.githooks/dw setup apply --proposal "$(jq -r .proposal_id .tmp/preview.json)" --expect "$(jq -r .expect .tmp/preview.json)" | jq '{outcome, journey_state}'`
Enter
Set TypingSpeed 30ms
Wait+Screen@60s /configured/
Sleep 3s

Hide
Type "clear"
Enter
Show
Type "# The roadmap project now exists on disk."
Enter
Type "find pm -maxdepth 3 -name '*.md' | head -6"
Enter
Sleep 3s

Hide
Type "clear"
Enter
Show
Type "# Every commit passes the gate: stage, lease a contract, certify it by hand, commit."
Enter
Type "git add -A && .githooks/dw step tic-tac-toe --json > .tmp/step.json && jq -r '.action.id' .tmp/step.json"
Enter
Wait+Screen@30s /generate-contract/
Type `eval "$(jq -r '.apply_command | @sh' .tmp/step.json)" > /dev/null && head -14 .tmp/CONTRACT.md`
Enter
Sleep 4.5s

Hide
Type "clear"
Enter
Show
Type "# The operator verifies each rule and flips the boxes. Consent is manual by design."
Enter
Type `sed -i '' 's/- \[ \]/- [x]/' .tmp/CONTRACT.md`
Enter
Type "git commit -m 'Adopt Tic Tac Toe: roadmap and governed delivery program'"
Enter
Wait+Screen@30s /Commit proceeding/
Sleep 3.5s
