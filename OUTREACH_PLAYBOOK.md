# The Outreach Playbook

Finding an expert is the easy 20%. Getting a busy, senior scholar to *reply* is
the 80%. This is the judgment the agent tries to encode — the same principles a
good chief of staff uses when recruiting people who get 200 cold emails a week.

> Context for this repo: I once recruited 10+ Nobel laureates to speak at a
> global science program **at zero honorarium**. None of them replied because of
> a clever subject line. They replied because the ask was specific, respectful of
> their time, and clearly worth their attention. That's what this codifies.

## The seven rules the drafts follow

1. **Specificity beats flattery.** Open with a real reference to *their* work — a
   paper, a talk, a result — not "I'm a huge admirer of your research." Anyone can
   fake admiration; only a real reader cites the actual thing.
2. **Earn the second sentence.** The first line has one job: prove this isn't a
   mass email. If it could have been sent to 500 people, rewrite it.
3. **One ask, low friction.** Ask for *one* small thing (a 20-minute call, a
   yes/no, an intro), never a menu. The easier it is to say yes, the more yeses.
4. **Lead with what's in it for them.** Senior experts are not short on work; they
   are short on *interesting, well-paid, flexible* work with real impact. Say that
   plainly.
5. **Credibility in one clause.** Who you are and why you're legitimate, in a
   phrase — not three paragraphs of company boilerplate.
6. **Under 130 words.** Length reads as low-effort-but-long. Short reads as
   respectful. If they're interested, the detail comes on the call.
7. **No manufactured urgency, no fake warmth.** No "quick question," no invented
   mutual friends, no "circling back." Trust compounds; tricks don't.

## What the agent does NOT do

- It doesn't send anything. It **drafts**; a human reviews and sends. Personal,
  reviewed outreach is the whole point — automation is for the research, not the
  relationship.
- It doesn't mass-blast. The scoring exists precisely to help you send *fewer,
  better* messages to the *right* people.

## Tuning

The live prompt lives in [`expert_agent/outreach.py`](../expert_agent/outreach.py)
(`SYSTEM` + `_prompt`). Edit those to change voice, length, or the offer. The
offline template in the same file is the zero-key stand-in used by `--demo`.

## A quick self-check before you hit send

- Would this line make *me* stop scrolling if it were about my work?
- Have I removed every sentence that doesn't earn its place?
- Is the ask something they could say yes to in 5 seconds?
- Am I being honest about who I am and what I'm offering?

If yes to all four, send it. If not, the agent gave you a draft, not a decree —
rewrite the weak line.
