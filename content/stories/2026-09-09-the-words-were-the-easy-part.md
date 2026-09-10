---
id: 2026-09-09-the-words-were-the-easy-part
product: "rororo"
title: "The words were the easy part"
subtitle: "RoRoRo shipped in six languages. The translating took an afternoon; finding every place the product speaks took the rest of the week."
published: 2026-09-09
tagline: "I set out to translate an app. What I found was every place a product speaks, and every one of them breaks differently."
hero_image: /assets/stories/2026-09-09-words-easy-part/header.png
draft: false
---

<figure class="ed-figure ed-fullbleed">
  <img src="/assets/stories/2026-09-09-words-easy-part/header.png" alt="The words were the easy part. 6,102 strings, six languages, one afternoon." loading="lazy" />
</figure>

RoRoRo was stable, and that was the problem.

It is a multi-launcher for Roblox that I built, free and open source, and by the start of
September it did what it was supposed to do. Every feature I could think of next would make it
better for the people already using it. So instead of building one, I pulled the install report,
because I wanted to know who those people actually were.

**1,536 installs, and 43% of them from places that don't speak English.** Against a store
listing written entirely in English, for an app written entirely in English.

I built this for a game clan. I have never really stopped thinking of it that way. But the
report was describing somebody else. Kids in France and Poland and Brazil who had found an
English tool, installed it anyway, and worked it out on their own.

The audience had arrived before the language did.

That changes what the job is. Localization is usually catching up to a competitor. Here there
was nobody to catch. Every tool in this category is English-only, all of them, which meant
translating was not a chore near the bottom of a list. It was the only move on the board that
opened a door instead of decorating a room.

So the plan was obvious, and I was wrong about it in the way you are wrong about obvious things:
**translate the words.**

## You can't translate what you can't reach

Most of my app's writing was somewhere a translator could never get to.

The engine underneath, the part that does the actual work and has no screens in it, was handing
the interface **finished English sentences**. Not facts about what happened, sentences. "Failed
to obtain auth ticket." That is a wall, because the part of the program that owns the words was
nowhere near the part that knows what language you read.

Then I found something worse. The interface was making decisions by reading those sentences.
Somewhere in there, a screen chose which warning icon to show by checking whether an error
message contained the phrase "Roblox does not appear to be installed."

Which means a copy edit could break the app. Fix a typo, break a feature, and nothing tells you.
That had been sitting in code I would have told you I knew well.

I fixed that before I translated anything. The engine now hands over a category and the bare
facts, a version number and a count, and exactly one place in the app turns those into sentences.
Then a test that breaks the build if a sentence ever sneaks back into the engine, because a
boundary is only real if something holds it.

That is the first thing this project gave me that had nothing to do with language. It made me
separate what my program *means* from what my program *says*. Those had been tangled together
for months and I hadn't noticed.

## Half the words weren't where I was looking

Then the screens themselves. **480 sentences written into the layouts, and another 430 or so
assembled while the app runs.** Status lines, settings summaries, error text built on the spot.

That second number is the one I would have guessed wrong. After the first sweep was done and
shipped, I ran the app in another language and it was still about half English, because half of
what a person reads was never in a layout file at all.

The finished dictionary holds 1,017 entries. Only 488 of them are reachable from the screens. If
you sweep your layouts and call it finished, you have translated less than half your product,
and nothing will tell you.

## The part that cost me most was a decision that passed every test

The first sweep wired each screen to look up its text by name. That is the standard way to do it
here, and the lookup happens once, when the screen is first built. It worked. **All 2,040 tests
passed.** It shipped. Getting it running on the build server meant hand-building a tool to
generate part of it, because the one that normally does that job doesn't run there. I was
fairly pleased with myself. That was the hard part, solved.

Then I added a language picker.

The lookup happens once and never again. Nothing behind it can say *the language changed, ask
me again*. Every word on screen is correct for the language the app **started** in, and cannot
be told otherwise.

Nothing fails. Not a test, not the build, not startup. The bug only exists in the moment someone
switches language without restarting, which is the entire reason to have a picker.

So the whole phase came out. Every translated line in every screen, touched a second time. The
tool I was pleased with is deleted. *It passes and it ships* and *it is right* are different
claims, and I had only checked the first one.

The same trap wore a second costume. Two places in the app built their display text the first
time they were used, which quietly froze the language at that moment. Right on first look, wrong
forever after a switch, and it survives every test that starts in one language.

Both bugs share a shape worth naming. **They are invisible to everything except the person using
the feature you built them for.**

## Then translating took an afternoon

Twelve agents, a translator and a reviewer for each language, 532 new entries across six.

The reviewers did real work rather than nodding along. Russian and Polish count differently than
English does, and they caught places where the translation had kept an English shape that doesn't
exist in those languages. A French line got rephrased so it stays correct whether the thing it
names turns out masculine or feminine. Brazilian Portuguese got a comma where English has a
decimal point, to match the numbers the app actually prints. None of that is something a checker
can find, and none of it is guessable from the English.

Then the boring machinery that makes it hold: check every dictionary, refuse to build if one is
short, regenerate everything. **1,017 entries across six languages. 6,102 translated strings.**
All complete, or nothing ships.

The moment it became real for me wasn't a test passing. It's that the app just follows whatever
language your computer is set to. A kid in Warsaw who updates doesn't find a setting or read an
announcement. They open it and it's in Polish. Nobody asked them anything.

When I wrote about this app in May I said it was for the kids who don't even know they're going
to play yet. I meant it as a thing about time. It turns out some of them were already here, and
what they didn't know yet was that it could talk to them.

## Why it took two tools

Structure and meaning are different problems, and one tool can't hold both.

**Vibe-Lingual handles structure.** I shipped it in June, eleven weeks before any of this, and
it does the mechanical work: pull the words out of the screens, keep every language's dictionary
complete, refuse to build when one is short, and fail loudly if raw English creeps back in. For
this app it needed a new adapter, because different Windows frameworks disagree about where
translated text lives. Its check on the fill-in-the-blank slots inside a sentence, the places a
name or a number gets dropped in, has never once been wrong across six languages.

What it can't do is tell you whether the words are right. Nothing mechanical can.

**So Translation Verification got built alongside it, and it handles meaning.** It started as a
review prompt and an approval step inside the app's own repo, became its own project the next
day, and had its first findings filed against it the day after that. It reads a translation
against the English and asks whether it still says the same thing, whether it sounds like a
person wrote it, whether anything got quietly dropped. Nothing ships until a human signs it off.
It caught a missing word in a security warning that no mechanical check could ever catch,
because nothing was structurally wrong with the sentence.

It's also the expensive one. It struggles on a full dictionary, and it returned **ten matters of
taste for every five real defects.** The taste ones are louder, because there are more of them.

Which gives you a rule for deciding where a problem belongs: **could a dumb check have caught
it?** Missing slots, incomplete dictionaries, grammar forms that never get used, all structure,
all cheap, all belong in the mechanical tool. Sending those to a model is slow, noisy, and buries
the findings that actually needed judgment. A missing word in a warning about your account is the
other kind, and it's worth all the noise.

They also make each other better, which is the entire reason they exist as a pair. Findings from
one run turned into fixes in both projects.

Here's the version of that I can point at. One suggestion that came out of reviewing the app was
that when a problem turns up in one language, you should go check the other five before you close
anything. That's now a standing rule in the reviewer's own instructions. It caught things a week
later that it would have walked straight past before. That's what these tools are built to do:
every real run leaves both of them sharper than it found them, so the next thing I point them at
gets the version that already learned this.

## The near-miss was a search box

I almost blew the last mile anyway, and I want it written down.

Store listings are per-language, and I'd translated the descriptions, the feature lists, the
what's-new. Then, while building a tool to help me paste ten listings across sixteen fields in
languages I can't proofread, I noticed the **keywords** were still in English on all six.

Keywords are the search box. English there doesn't read oddly. It makes you **invisible**. A
Polish kid types *wiele instancji* and my beautifully translated listing isn't in the results at
all. Hours before submission, and the tool caught it, not me.

The right keywords weren't translations either. *launcher* stays English in every one of them,
because that's the word those communities actually type. Russian gets *роблокс* in Cyrillic,
because that's how people there spell it into a box. Translating the words would have been the
wrong job.

## Running the same check three times

Here's the thing I didn't expect to learn, and the thing I'd want most if I were reading this
instead of writing it.

We ran the reviewer over the same slice three times. Same 306 translations, same instructions,
nothing carried over between runs. It came back with **six problems, then thirteen, then five.**
Sixteen different ones across all three runs, and **eleven of those showed up in exactly one
run.**

Sorted out afterward: five real defects, one that was flat wrong, ten matters of taste. Ten of
sixteen were opinions. Defensible either way, not worth a translator's time, and loud enough to
bury the rest.

The split lines up almost exactly with repetition. **The problems that survive being asked again
are real. The ones that appear once and then don't are usually taste.** Almost, and the
exceptions matter: one real defect showed up only once, and the wrong one showed up twice. But
repetition is the signal, not how certain the model sounds, which turned out to mean nothing at
all.

Asking once is taking a sample, not getting an answer. If you're going to trust a machine to
read a language you can't, ask it more than once and believe the things that keep coming back.

## The one missing word

The problem that survived all three runs, in French and Spanish and again in German: the warning
that appears when you export your account file says *don't post the file publicly*, and all three
translations dropped **publicly**.

That's the warning attached to your logins. It shipped, the tool caught it, it's fixed.

Two more were Polish. Sixteen entries used a grammatical form that only applies to fractions,
sitting in places that count whole things and can never reach it. Real grammar errors, in
sentences **no one can ever see.** We fixed them anyway, wrote down in the same breath that
nobody could reach them, and then filed it against the reviewer so it stops spending anyone's
attention there.

Fixing a bug nobody can hit, and then making sure nobody has to look again, is a better ending
than catching one.

One finding was simply wrong, and it's the most useful of the lot. The tool flagged a German
sentence for moving its fill-in-the-blank slots around compared to the English. The move is
required. German puts the verb at the end, and everything else shuffles to make room. Any check
that cares about order will trip on perfectly good German, and on Japanese, and on Turkish. What
matters is that nothing went missing, not the order things arrive in.

What killed that finding was a person sitting down and working through German sentence order.
Which is the real lesson. **A complaint about a language nobody on your team reads is the most
expensive kind to wave off, and the only thing that lets you wave it off safely is doing the
grammar.** That's an argument for tools that show their reasoning inside the finding, so you can
check the work without first becoming a German speaker.

## It kept spreading outward

The app, then the listing. Then the screenshot captions, and one of them said *its own Stop
button* while the Polish app now says *Zatrzymaj*, so the caption had to stop quoting the app and
start describing it. Then the trailer, whose on-screen cards needed their boxes measured, because
German runs long and a fixed box clips. Then the narration, which is a different problem again: a
card is limited by **width**, a voiceover by **time**, and Spanish needs about a third more
syllables to say the same thing. Twenty of forty-two lines came back too long on the first pass.

The reviewer came with me to every one of those, and it needed a different lens each time. For the
trailer it stopped counting characters and started counting syllables, because the limit had
stopped being a box and started being a breath. It had to flag lines that read fine on a page and
trip in the mouth. And it had to learn a kind of wrong it had never been asked to look for: an
intensifier that lands harder in another market than it does in English, a phrase a local
advertising ear would hear as a promise about safety. That last one matters more than it sounds.
It's a claim I'm not entitled to make, and I'm not entitled to make it in six languages either.

One of the lines it checked was mine. *Imagine Something Else* had never existed in another
language. It came back as *Imagine autre chose*, and *Imagina algo diferente*, and *Imagine algo
diferente*. German, Polish, and Russian keep the English on purpose, because the line lands better
there left alone than rendered. Same lesson as the search box, arriving from the other direction:
knowing which words to leave in English is half of knowing how to translate.

The trailers are built. Six languages, my voice in all of them.

I set out to translate an app. What I actually did was find every place the product speaks,
screens and errors and store copy and search terms and a picture's caption and a voice, and find
out they each break differently, and that the words were never the hard part in any of them.

v1.27 passed certification. It's live.

Somewhere a kid in Warsaw is opening it in Polish, and has no idea any of this happened. Which is
the whole point.
