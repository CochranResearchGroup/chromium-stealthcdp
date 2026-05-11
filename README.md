# chromium-stealthcdp

Patch queue for Chromium customizations related to stealth CDP behavior.

## Layout

- `upstream-revision.txt` records the Chromium base commit this queue is built on.
- `patches/` contains `git format-patch` output exported from `../src`.

## Working Branch

Development happens in the Chromium checkout at `../src` on branch:

```sh
ec/chromium-stealthcdp
```

## Export

From `../src`, export the current patch queue with:

```sh
rm -f ../chromium-stealthcdp/patches/*.patch
git format-patch --binary -o ../chromium-stealthcdp/patches "$(cat ../chromium-stealthcdp/upstream-revision.txt)..HEAD"
```

Then commit the updated patch files in this repository.

## Apply

From another Chromium `src` checkout at the recorded base revision or a compatible
descendant:

```sh
git am /path/to/chromium-stealthcdp/patches/*.patch
```
