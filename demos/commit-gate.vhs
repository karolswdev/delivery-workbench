Output demos/rendered/commit-gate.gif

Set Shell "bash"
Set FontSize 15
Set Width 1100
Set Height 760
Set Theme "Dracula"
Set TypingSpeed 35ms

Type "bash demos/scripts/prepare-commit-demo.sh"
Enter
Sleep 2s

Type "cd /tmp/delivery-workbench-commit-demo"
Enter
Type "echo 'A small delivery note for the demo.' > delivery-note.txt"
Enter
Type "git add delivery-note.txt"
Enter
Type "git commit -m 'add delivery note'"
Enter
Sleep 2s

Type ".demo/write-contract yes 'Shows the commit gate keeping the model honest.'"
Enter
Type "git commit -m 'add delivery note'"
Enter
Sleep 1s

Type ".demo/show-log"
Enter
Sleep 2s
