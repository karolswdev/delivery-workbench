Output demos/rendered/segments/04-grant.mp4

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

Type "# Start the story through the same deliberate-step rail. Same ritual every time."
Enter
Set TypingSpeed 10ms
Type `.githooks/dw step tic-tac-toe --json > .tmp/step.json && jq -r '.action.id' .tmp/step.json && eval "$(jq -r '.apply_command | @sh' .tmp/step.json)" > /dev/null`
Enter
Wait+Screen@30s /start-story/
Type `git add -A && .githooks/dw step tic-tac-toe --json > .tmp/step.json && eval "$(jq -r '.apply_command | @sh' .tmp/step.json)" > /dev/null && sed -i '' 's/- \[ \]/- [x]/' .tmp/CONTRACT.md && git commit -q -m 'Start TTT-1-01' && echo COMMITTED"-ok"`
Enter
Wait+Screen@30s /COMMITTED-ok/
Set TypingSpeed 30ms
Sleep 2s

Hide
Type "clear"
Enter
Show
Type "# Now the grant. Every capability and budget is named. Nothing is implied."
Enter
Set TypingSpeed 4ms
Type ".githooks/dw program plan tic-tac-toe-generated-program --mode checkpointed --operator karol --reason 'Deliver TTT-1-01 through one bounded cross-provider grant.' --intent ceremony --expires-in 3600 --capability program:select --capability agent:dispatch --capability check:execute --capability workspace:write --capability verdict:issue --capability knowledge:lesson-writeback --budget max_phases=1 --budget max_stories=1 --budget max_child_runs=8 --budget max_agent_starts=8 --budget max_provider_starts=8 --budget max_model_starts=8 --budget max_check_starts=4 --budget max_loop_rounds=4 --budget max_debate_rounds=1 --budget max_councils=1 --budget max_repairs_per_story=1 --budget max_verdicts=2 --budget max_obligations=2 --budget max_obligation_materializations=1 --budget max_obligation_dispositions=2 --budget max_integrations=1 --budget max_commits=1 --budget max_pushes=1 --budget max_nudges=1 --budget max_lessons=1 --budget max_lesson_writebacks=2 --budget max_artifact_bytes=24320000 --budget max_tokens=1100000 --budget max_observed_cost_microunits=15000000 --budget max_wall_seconds=27000 --json > .tmp/plan.json"
Enter
Set TypingSpeed 30ms
Sleep 1s
Type "jq '{applicable, capabilities: .authority.capabilities, expires: .authority.expires_at}' .tmp/plan.json"
Enter
Sleep 4s

Hide
Type "clear"
Enter
Show
Type "# Commit, push, merge, release, publish are not in the list. They cannot be granted here."
Enter
Sleep 2s

Hide
Type "clear"
Enter
Show
Type "# Approve the finite grant. This is the second human approval."
Enter
Set TypingSpeed 10ms
Type `.githooks/dw program start --plan .tmp/plan.json --expect "$(jq -r .start_token .tmp/plan.json)" --approve --json > .tmp/start.json`
Enter
Set TypingSpeed 30ms
Type "jq '{run_id, state}' .tmp/start.json"
Enter
Wait+Screen@30s /running/
Sleep 3.5s
