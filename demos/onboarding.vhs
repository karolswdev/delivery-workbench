Output demos/rendered/onboarding.gif

Set Shell "bash"
Set FontSize 15
Set Width 1100
Set Height 760
Set Theme "Dracula"
Set TypingSpeed 35ms

Type "bash demos/scripts/prepare-onboarding-demo.sh"
Enter
Sleep 2s

Type "cd /tmp/delivery-workbench-onboarding-demo"
Enter
Type ".demo/session-intake . --project-name 'Demo App' --project-slug demo-app --project-prefix DEMO"
Enter
Sleep 500ms

Type "3"
Enter
Type "2,3,4"
Enter
Type "1"
Enter
Type "2"
Enter
Type "2,5"
Enter
Type "Bootstrap this running project into an actionable roadmap."
Enter
Type "Preserve current behavior while adding delivery discipline."
Enter
Type "1"
Enter
Type "A future agent should know the next step and the proof commands."
Enter
Type "Session intake and adoption prompt exist with clear intent."
Enter
Type "Do not invent product goals."
Enter
Type "This repo is already in flight."
Enter
Type "Read-only discovery first."
Enter
Type "Which tests prove the project is healthy?"
Enter
Type "Y"
Enter
Sleep 500ms

Type ".demo/adopt-project . --project-name 'Demo App' --project-slug demo-app --project-prefix DEMO --require-intake"
Enter
Sleep 500ms

Type "sed -n '1,56p' pm/roadmap/demo-app/adoption/session-intake.md"
Enter
Sleep 2s
