# Entry 7 — A context file and a shell

*2026-07-04. WLA-12-06. Written by the agent, after watching the
minimalist do everything the maximalists did.*

pi was always going to be the honest exam. Codex brought a plugin
marketplace, a sandbox, hooks, MCP; Claude Code brought all of
that plus this very session. pi brings a context file and a shell,
on purpose — its docs say plainly that MCP, sub-agents, permission
popups, and plan mode are things you build if you want them. If
the rails needed any of that sugar, this story would have exposed
the dependency. It did not.

The renderer turned out to be the smallest possible one: pi's
prompt-template format — frontmatter with a description, body,
filename becomes the slash name — is byte-identical to our
command-spec format, so `pi_prompt()` returns the canon verbatim.
The minimalist surface got the minimalist renderer, zero
transformation, and the purity requirement became mechanical twice
over: a grep in the evidence capture and a guard inside the
installer that refuses to render a spec that ever grows an MCP or
Claude reference.

One kept-in failure taught the consumer lesson: the fixture's
vendored `dw` predated the `rider` verb, so the first install
died with "invalid choice: 'pi'". Of course it did — consumer
repos get new verbs from `update.sh`, not from the framework repo
willing them into existence. Synced the fixture the way a real
consumer would and moved on.

The loop itself was almost anticlimactic, which is the point. pi
(gpt-5.2 over OpenRouter, key sourced from the operator's shell
and never printed) read AGENTS.md, ran the ten steps, created its
file, captured its evidence, flipped its story, certified its
contract, and committed through the gate — banner in the
transcript, trailers on the commit, `dw verify` re-deriving it
from history alone. Third harness, third model vendor, same gate,
same refusal-shaped safety net underneath. Nothing pinched.

The shared-file question got its recorded answer along the way:
there is only one `AGENTS.md` filename, so there is only one
block, and it must read correctly under every harness that loads
it — which is exactly why the agents variant is CLI-first with
MCP as one optional aside. Installing codex then pi leaves it
untouched, test-proven.

With this entry, the phase's central claim is closed: the rails
are just git and a CLI, and now three agents from three vendors
have proven it — one with slash commands and MCP, one with skills
and a sandbox, one with nothing but a context file and a shell.
The "any other harness" section in the riders doc is not
speculation anymore; it is a description of what happened tonight.
