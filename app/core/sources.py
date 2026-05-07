#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Built-in text sources for matrix rain messages."""

import sys
from pathlib import Path


HAMLET = """To be, or not to be, that is the question:
Whether 'tis nobler in the mind to suffer
The slings and arrows of outrageous fortune,
Or to take arms against a sea of troubles,
And by opposing end them. To die, to sleep
No more; and by a sleep to say we end
The heart-ache and the thousand natural shocks
That flesh is heir to: 'tis a consummation
Devoutly to be wish'd. To die, to sleep;
To sleep, perchance to dream ay, there's the rub:
For in that sleep of death what dreams may come,
When we have shuffled off this mortal coil,
Must give us pause there's the respect
That makes calamity of so long life.
The undiscovered country, from whose bourn
No traveller returns, puzzles the will,
And makes us rather bear those ills we have
Than fly to others that we know not of?
Thus conscience does make cowards of us all,
And thus the native hue of resolution
Is sicklied o'er with the pale cast of thought,
And enterprises of great pith and moment
With this regard their currents turn awry
And lose the name of action.
Something is rotten in the state of Denmark.
Though this be madness, yet there is method in't.
Brevity is the soul of wit.
There are more things in heaven and earth, Horatio,
Than are dreamt of in your philosophy.
Good night, sweet prince, and flights of angels sing thee to thy rest.
The lady doth protest too much, methinks.
Frailty, thy name is woman.
What a piece of work is man! How noble in reason,
how infinite in faculty, in form and moving how express
and admirable, in action how like an angel,
in apprehension how like a god! The beauty of the world,
the paragon of animals and yet, to me,
what is this quintessence of dust?
We know what we are, but know not what we may be.
There is nothing either good or bad, but thinking makes it so.
Doubt thou the stars are fire,
Doubt that the sun doth move,
Doubt truth to be a liar,
But never doubt I love."""


LOREM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit,
sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
Sed ut perspiciatis unde omnis iste natus error sit voluptatem
accusantium doloremque laudantium, totam rem aperiam, eaque ipsa
quae ab illo inventore veritatis et quasi architecto beatae vitae
dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit
aspernatur aut odit aut fugit, sed quia consequuntur magni dolores
eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est,
qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit,
sed quia non numquam eius modi tempora incidunt ut labore et dolore
magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis
nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut
aliquid ex ea commodi consequatur. Quis autem vel eum iure
reprehenderit qui in ea voluptate velit esse quam nihil molestiae
consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla
pariatur. At vero eos et accusamus et iusto odio dignissimos ducimus
qui blanditiis praesentium voluptatum deleniti atque corrupti quos
dolores et quas molestias excepturi sint occaecati cupiditate non
provident, similique sunt in culpa qui officia deserunt mollitia
animi, id est laborum et dolorum fuga."""


def read_binary_as_hex(path: Path, max_bytes: int = 4096) -> str:
    """Read any file as raw bytes and return hex representation.

    Every file is bytes. This reads them and converts to their
    hexadecimal string form. Works on anything: text, PDFs, images,
    executables, whatever. Pure Python, no third-party dependencies.
    """
    with open(path, 'rb') as f:
        raw = f.read(max_bytes)
    return ' '.join(f'{b:02x}' for b in raw)


def get_matrix_hex() -> str:
    """Read the matrix tool's own source as raw bytes, return hex.

    In dev mode: reads main.py bytes.
    In compiled (Nuitka) mode: reads the executable.
    Either way, you see the raw data behind the matrix.
    """
    exe = Path(sys.executable)
    if exe.is_file() and exe.stat().st_size > 0:
        base = Path(__file__).resolve().parent.parent
        main_file = base / "main.py"
        if main_file.is_file():
            return read_binary_as_hex(main_file, max_bytes=8192)
    return read_binary_as_hex(Path(sys.executable), max_bytes=8192)


def get_source(name: str, path: str = None) -> str:
    """Get text content for a named source.

    Args:
        name: One of 'hamlet', 'lorem', 'matrix'.
        path: Optional file path for --matrix to read as binary.

    Returns:
        Text string to feed into the rain message injector.
    """
    if name == 'hamlet':
        return HAMLET

    if name == 'lorem':
        return LOREM

    if name == 'matrix':
        if path:
            target = Path(path)
            if not target.is_file():
                raise FileNotFoundError(f"{path}: No such file")
            return read_binary_as_hex(target)
        return get_matrix_hex()

    raise ValueError(f"Unknown source: {name}")
