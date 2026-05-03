# matrix

Matrix digital rain effect for your terminal.

Version: 0.1.0

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

# Show help
matrix -h

# Show version
matrix -v
```

## Keybindings

| Key | Action |
|-----|--------|
| q / Q / Esc | Quit |

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
