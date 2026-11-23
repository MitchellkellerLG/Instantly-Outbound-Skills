# Contributing

Pull requests and issues are welcome.

- One skill per folder under `skills/`, with a `SKILL.md` (name and description in the front matter) and a short `README.md` for people using it by hand.
- Skills should only write text or files on the user's machine. No hidden network calls, no tracking, and nothing that sends, launches or spends on someone's account without their explicit OK.
- Never commit real customer names, email addresses, API keys, tokens or private links. Use example.com style placeholders.
- Keep the language plain and short. Say what the skill does, not what it might do.
- Before opening a pull request, run a secret scan such as `gitleaks detect --source .`.
