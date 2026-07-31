# EnjoyPython

> *What if God is the programmer of all? Everything that has been programmed has free will.*

---

## 📋 Table of Contents
- [About](#about)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## 📚 About

A hobby project exploring **game theory** concepts through Python implementation. This project is in early development stage, building foundational structures for game theory simulations and analysis.

**Philosophical Context:** Inspired by the idea that programmed systems, much like our universe, possess emergent properties and complex behaviors that simulate autonomy and free will.

---

## ✨ Current Features

- **GameTheory class** - Core framework for managing players and game payoffs
- Player management system
- Payoff tracking and retrieval
- Modular structure for extending game mechanics
- *More features coming soon...*

---

## 📁 Project Structure

```
enjoyPython/
├── README.md                          # Project documentation
├── the-game-theory/                   # Game theory implementations
│   └── main.py                        # GameTheory class (player & payoff management)
└── .venv/                             # Python virtual environment
```

**Current Files:**
- `the-game-theory/main.py` - Contains the `GameTheory` class for managing players and game payoffs

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

```bash
# Clone the repository
git clone https://github.com/Reniel-Relearn/life-creation.git

# Navigate to the project
cd enjoyPython

# Install dependencies (if any)
pip install -r requirements.txt
```

---

## 💻 Usage

### GameTheory Class

The `GameTheory` class provides a framework for:
- Adding players to a game
- Setting and retrieving payoff values between players
- Managing game state

### Example (Coming Soon)

```python
from the-game-theory.main import GameTheory

# Create a game
game = GameTheory()

# Add players
game.add_player("Player 1")
game.add_player("Player 2")

# Set payoffs
game.set_payoff("Player 1", "Player 2", (3, 2))

# Get payoff
payoff = game.get_payoff("Player 1", "Player 2")
print(payoff)  # Output: (3, 2)
```

**Note:** Game simulation logic (`.play()` method) is under development.

---

## 📦 Requirements

**Python Version:** 3.8+

**Dependencies:** Currently none (core Python only)

To add dependencies in the future:
```bash
pip freeze > requirements.txt
```

---

## 🎓 Project Goals

- Build foundational game theory simulations in Python
- Explore how programmed systems exhibit emergent behavior
- Implement classic game theory concepts (Prisoner's Dilemma, Nash Equilibrium, etc.)
- Create reusable game framework for experimentation

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Reniel Galang**
- GitHub: [@Reniel-Relearn](https://github.com/Reniel-Relearn)
- Email: plaisolutionsph@gmail.com

---

## 📞 Support

For questions or issues, feel free to:
- Open an GitHub Issue
- Contact me via email
- Check the project discussions

---

**Status:** 🚧 Early Development
**Last Updated:** July 31, 2026
