Output demos/rendered/segments/02-intake.mp4

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

Type "# The idea: two browsers, one game of Tic Tac Toe, over WebSockets."
Enter
Type "# The scope conversation (/dw-scope in Claude Code) drafted one inert proposal:"
Enter
Type "mkdir -p .tmp && cp ../assets/setup-proposal.json .tmp/setup-proposal.json"
Enter
Type "jq '{project, state, starts_work, creates_grant, certifies, commits}' .tmp/setup-proposal.json"
Enter
Sleep 3.5s

Hide
Type "clear"
Enter
Show
Type "# Closed intake answers pick the delivery team and the checks."
Enter
Type "cp ../assets/answers.json answers.json && jq '{profiles, verification, autonomy_mode}' answers.json"
Enter
Sleep 3.5s

Hide
Type "clear"
Enter
Show
Type "# The scaffold compiles idea + answers into one governed bundle. Still inert."
Enter
Set TypingSpeed 10ms
Type `.githooks/dw program scaffold --answers answers.json --proposal .tmp/setup-proposal.json --json > .tmp/proposal.json && echo SCAFFOLD"-ok"`
Enter
Set TypingSpeed 30ms
Wait+Screen@30s /SCAFFOLD-ok/
Type "jq '{program: .tracked_content.policy.program.document.slug, riders: (.local_content.driver_bindings | keys), starts_work, creates_grant}' .tmp/proposal.json"
Enter
Sleep 4s

Hide
Type "clear"
Enter
Show
Type "# Nothing outside .tmp/ was written. Review happens in the Workbench, in a browser."
Enter
Sleep 2.5s
