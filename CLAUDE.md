# Before anything else: use a worktree, not this checkout

This directory (`McCormacks-Site`) is the shared main checkout. Multiple
Claude sessions work this repo at the same time. Before editing any file,
set up your own worktree and branch:

```sh
git worktree add ../mccormacks-<session> -b <session>/<topic> main
ln -s "$PWD/node_modules" ../mccormacks-<session>/node_modules
```

Then work, render, test and commit inside that worktree — never in this
directory. Land finished work with a fast-forward merge from here:

```sh
cd "<this checkout>" && git merge --ff-only <session>/<topic> && git push origin main
```

Full detail — why, what breaks if you skip it, how to land when `main` has
moved, per-session preview ports — is in
`setup/MAINTENANCE.md`, under "Read this first: parallel sessions". Read
that section before your first commit. This has already caused three
separate incidents from sessions editing this checkout directly; do not add
a fourth.
