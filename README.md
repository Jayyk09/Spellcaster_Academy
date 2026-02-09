# Spellcaster Academy

An interactive RPG game that teaches American Sign Language through gameplay! Cast spells using ASL hand gestures detected through your webcam and battle through waves of enemies while learning real ASL letters and words.

## Overview

American Sign Language is essential to bridging the communication gap between deaf and non-deaf individuals. Current methods of learning ASL are slow, easily forgettable, and non-engaging.

**Spellcaster Academy** aims to fix these problems by gamifying the process, bringing communities closer together through an interactive and addictive RPG experience!

## Features

- **Real-time ASL Recognition**: Use your webcam to cast spells with actual ASL hand gestures
- **Engaging RPG Gameplay**: Battle through waves of enemies with spell-based combat
- **Educational & Fun**: Learn ASL naturally while playing an exciting game
- **Custom AI Model**: Built-from-scratch computer vision model trained for accurate gesture recognition
- **Expandable**: Easily add new ASL letters, words, and game content

## Quickstart

### Prerequisites

- Python 3.8 or higher
- Webcam (for ASL gesture detection)
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Jayyk09/Spellcaster_Academy.git
cd Spellcaster_Academy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Game

Simply run the main game file:
```bash
python main.py
```

The game will start, and you can use your webcam to perform ASL gestures to cast spells!

### Controls

- **Webcam**: Perform ASL hand gestures to cast spells
- **Mouse**: Navigate menus and UI
- **ESC**: Pause/Menu

## How It Was Built

- **Game Engine**: Built using PyGame for the core game mechanics, rendering, and game loop
- **Computer Vision**: Custom AI model built with:
  - **OpenCV**: Image processing and webcam input
  - **MediaPipe**: Hand landmark detection
  - **NumPy**: Data processing and numerical operations
  - **scikit-learn**: RandomForest classifier for gesture recognition
- **Architecture**: Custom-trained model on our own dataset for accurate ASL recognition
- **Performance**: Threading and OS-level optimizations to run both CV model and game loop at high FPS

## Project Structure

```
Spellcaster_Academy/
├── main.py              # Game entry point
├── core/                # Core game systems (camera, tilemap, etc.)
├── entities/            # Game entities (player, enemies, spells)
├── scenes/              # Game scenes (menu, world)
├── vision/              # ASL detection and computer vision
├── assets/              # Game assets (sprites, sounds, fonts)
├── config/              # Configuration files
└── data/                # Game data (waves, maps)
```

## Accomplishments

None of us had ever built ground-up AI models or games in a hackathon context, so there was a ton of learning required to get a polished final product. We're incredibly proud of how fun and useful Spellcaster Academy turned out!

## What We Learned

As relative newcomers to game development and machine learning engineering, we all learned a ton about the fields and how to produce a quality product in such a short period of time. Key learnings include:

- Building and training custom computer vision models from scratch
- Architecting a full game engine with PyGame
- Optimizing performance with threading for real-time applications
- Balancing educational content with engaging gameplay

## What's Next

The architecture of both the model and the game itself allows for incredibly easy configuration:
- **Add new ASL gestures**: Just ~30 seconds of webcam captures per letter/word
- **Train the model**: ~15 seconds for training
- **Add game content**: A few lines changed in `waves.json` to add more enemies and waves

We would love to use this ease of expansion to cover even more ASL words and phrases, making Spellcaster Academy an even more comprehensive learning tool!

## Contributing

Contributions are welcome! Whether you want to add new ASL gestures, create new enemy types, or improve the game mechanics, feel free to submit a pull request.

## Acknowledgments

Built with passion during a hackathon to make ASL learning accessible and fun for everyone!

---

**Ready to become an ASL Spellcaster?** Start your journey now!
