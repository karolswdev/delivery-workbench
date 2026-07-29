Output demos/rendered/segments/01-init.mp4

Require dw
Set Shell "bash"
Set FontSize 16
Set Width 1280
Set Height 720
Set Theme "Dracula"
Set TypingSpeed 30ms

Hide
Type "source /tmp/dw-ceremony-demo/env.sh && clear"
Enter
Show

Type "# One empty directory. No roadmap, no rails, no project."
Enter
Type "mkdir tic-tac-toe && ls -la tic-tac-toe"
Enter
Sleep 1.5s

Type "# The front door: one command installs the rails."
Enter
Type `dw init tic-tac-toe | tail -n 4 && echo INIT"-ok"`
Enter
Wait+Screen@60s /INIT-ok/
Sleep 2.5s

Type "cd tic-tac-toe"
Enter

Type "# The desk's validated rider roster (configuration, not permission)."
Enter
Type "mkdir -p .git/pmo-orchestration && cp ../assets/drivers.json .git/pmo-orchestration/drivers.json"
Enter
Type "jq '.profiles | keys' .git/pmo-orchestration/drivers.json"
Enter
Wait+Screen@15s /codex-verifier/
Sleep 2s

Type "# Are the rails healthy?"
Enter
Type `clear && .githooks/dw doctor | tail -n 16 && echo DOCTOR"-ok"`
Enter
Wait+Screen@60s /DOCTOR-ok/
Sleep 3.5s
