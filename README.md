XLIFF parser (for iOS)
---

A (simple) script that helps with importing an XLIFF file into an iOS project.
It solves the problem of importing localizations when you are using a
(descriptive) pseudo-language as keys, rather than the development language. In
that case, the XLIFF file exported by tools such as Lokalise or Applanga ends up
using the development language rather than the keys in the XLIFF <source> tags,
which messes up the import. This scripts fixes this, then import directly the
files into the iOS project.

Use:

``python parse_xliff.py -i <path/to/xliff/file> -o <path/to/project/root>``
