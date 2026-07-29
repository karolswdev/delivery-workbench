Output demos/rendered/segments/05-live.mp4

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

Type "# Live delivery: claude implements, codex verifies. Each act is previewed, then leased."
Enter
Type "echo $RUN"
Enter
Sleep 1.5s
Set TypingSpeed 10ms
Type ".githooks/dw program preview $RUN supervise --max-ticks 100 --max-seconds 1500 --json > .tmp/sup-preview.json && jq '{applicable, act_token}' .tmp/sup-preview.json"
Enter
Sleep 3s
Type `.githooks/dw program supervise $RUN --expect "$(jq -r .act_token .tmp/sup-preview.json)" --max-ticks 100 --max-seconds 1500 --json > .tmp/supervise.json ; jq '{stop, ticks: .tick_count, terminal}' .tmp/supervise.json && echo SUPERVISE"-over"`
Enter
Set TypingSpeed 30ms
Wait+Screen@28m /SUPERVISE-over/
Sleep 2s

Type ".githooks/dw program show $RUN | head -16"
Enter
Sleep 6s
