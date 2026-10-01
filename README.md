# Smart Files Organizer

A desktop app that sorts messy folders by file type, with preview and undo.

Pick a folder, see exactly where every file will go, then organize it with one click. If you change your mind, undo restores everything.

## Features

- **Preview first:** see every file and its destination before anything moves
- **Color-coded file types:** Images, Videos, Music, Documents, Archives, Applications and Others
- **Breakdown bar:** see how your folder splits by type at a glance
- **Filter:** search the preview by file name or type
- **One-click undo:** moves files back and removes the folders it created
- **Safe by design:** never overwrites files (duplicates are renamed `name_1.ext`), skips hidden files, and keeps going if one file can't be moved
- **Keyboard shortcuts:** `Ctrl+O` to choose a folder, `Ctrl+Z` to undo

## Requirements

- Python 3.8 or newer
- No extra packages. It uses only the standard library (Tkinter).

## How to run

```bash
python organizer.py
```

## How to use

1. Click **Choose folder** and select the folder you want to tidy.
2. Check the preview to see where each file will go.
3. Click **Organize files** and confirm.
4. Click **Undo last** if you want everything back where it was.

## Supported file types

| Category | Extensions |
|---|---|
| Images | .jpg .jpeg .png .gif .bmp .webp .svg |
| Videos | .mp4 .mkv .avi .mov .wmv |
| Music | .mp3 .wav .flac .aac .ogg |
| Documents | .pdf .doc .docx .txt .ppt .pptx .xls .xlsx |
| Archives | .zip .rar .7z .tar .gz |
| Applications | .exe .msi |
| Others | everything else |

To add or change types, edit the `FILE_CATEGORIES` dictionary at the top of the script.

## License

MIT
