# matrix

```
    ﾀ           ﾎ       0           ﾐ       ﾘ
    ﾗ       ﾂ   ﾖ       1   ﾃ           ﾕ   ﾜ
    ﾊ       ﾓ   ﾑ       ﾌ   ﾒ       7   ﾋ   ﾄ
    ﾆ   9   ﾏ   ﾅ   ﾇ   ﾂ   ﾍ       ﾙ   ﾔ   ﾈ
    ﾂ   ﾀ   ﾘ   ﾃ   ﾌ   ﾊ   ﾖ   3   ﾎ   ﾑ   ﾓ
    ﾎ   ﾗ   ﾆ   ﾐ   ﾕ   ﾏ   ﾄ   ﾒ   ﾅ   ﾜ   ﾘ
    ﾖ   ﾊ   ﾑ   ﾔ   ﾃ   ﾆ   ﾙ   ﾍ   ﾋ   ﾇ   ﾀ
    ﾍ   ﾌ   ﾋ   ﾜ   ﾈ   ﾓ   ﾅ   ﾗ   ﾂ   ﾐ   ﾕ
```

Matrix digital rain effect for your terminal.

Version: 1.2.0

## Features

- **Authentic feel**: Half-width katakana, symbols, digits — like the movie
- **Depth layers**: Foreground and background streams at different brightnesses
- **Character mutation**: Characters flicker and change as they fall
- **Variable speed**: Each stream falls at its own pace
- **Bright head glow**: Leading characters shine white, fading to deep green
- **256-color support**: Rich green gradient with graceful 8-color fallback
- **Responsive**: Adapts to terminal resize in real time

## Usage

```bash
# Start the rain
matrix

# Embed a message in the rain
matrix follow the white rabbit

# Rain with hexadecimal characters only
matrix --hex

# Rain with binary characters only
matrix --bin

# Rain with decimal characters only
matrix --dec

# Rain with alphabet characters only
matrix --zed

# Rain with custom characters from a file
matrix --rain chars.txt

# Custom rain + message (use -- to separate)
matrix --rain emoji.txt -- wake up neo

# Rain Shakespeare's Hamlet
matrix --hamlet

# Rain Lorem Ipsum
matrix --lorem

# Rain hex of any file
matrix -x <file>

# Embed a file's contents
matrix -f document.txt

# Rain its own source code
matrix --self

# Show help / version
matrix -h
matrix -v
```

## Keybindings

| Key | Action |
|-----|--------|
| q / Q / Esc | Quit |
| r | Reverse rain direction |
| b | Burst effect |
| x | Scatter effect |

## Installation

### With pget
```bash
pget install matrix
```

### Build from source
```bash
git clone https://github.com/pynosaur/matrix.git
cd matrix
bazel build //:matrix_bin
cp bazel-bin/matrix ~/.local/bin/
```
