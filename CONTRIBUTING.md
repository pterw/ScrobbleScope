# Contributing to ScrobbleScope

First off, thank you for considering contributing to ScrobbleScope! Whether it's reporting a bug, suggesting an enhancement, or offering feedback, your input is valuable.

As this project is currently under active development and primarily maintained by a solo developer, the contribution process is kept straightforward.

## How Can I Contribute?

There are several ways you can contribute:

### Reporting Bugs

* If you find a bug, please ensure it hasn't already been reported by checking the [GitHub Issues](https://github.com/pterw/ScrobbleScope/issues) page.
* If it's a new bug, please open a new issue. Be sure to include:
    * A clear and descriptive title.
    * Steps to reproduce the bug.
    * What you expected to happen.
    * What actually happened (including any error messages or screenshots if applicable).
    * Your browser/OS (if relevant to a UI bug).

### Suggesting Enhancements or New Features

* We're open to ideas! If you have a suggestion for an enhancement or a new feature, please open an issue to discuss it.
* Provide a clear description of the feature, why it would be useful, and any potential implementation ideas you might have.

### Providing Feedback

* General feedback on usability, design, or functionality is also welcome. You can open an issue to share your thoughts.

### Pull Requests (For Future Consideration)

While direct code contributions via pull requests are not the primary focus at this early stage, if you have a fix or a small enhancement you'd like to propose:

1.  **Fork the Repository:** Create your own fork of `pterw/ScrobbleScope`.
2.  **Create a Branch:** Create a new branch in your fork for your changes (e.g., `git checkout -b feature/amazing-new-feature` or `fix/bug-description`).
3.  **Make Your Changes:** Implement your fix or feature.
    * Please try to follow existing code style (generally PEP 8 for Python).
    * Ensure your changes don't break existing functionality.
4.  **Commit Your Changes:** Write clear, concise commit messages.
5.  **Push to Your Fork:** Push your changes to your forked repository.
6.  **Open a Pull Request:** Submit a pull request to the `main` branch of `pterw/ScrobbleScope`.
    * Clearly describe the problem and solution. Include the relevant issue number if applicable.

Please note that as the project evolves, these guidelines for pull requests might become more detailed.

## Setting Up Your Development Environment

To get ScrobbleScope running locally for development, please refer to the "Getting Started" section in the [README.md](README.md). Key steps include:

1.  Cloning the repository.
2.  Setting up a Python virtual environment.
3.  Installing dependencies from `requirements.txt`.
4.  Creating a `.env` file with your API keys.
5.  Running `python app.py`.

For development, you might want to set `DEBUG_MODE="1"` in your `.env` file for more verbose logging and Flask's debug mode.

## Code Style (Python)

Please try to follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines for Python code. Most modern Python linters (like Flake8) can help check for this.

## CONDUCT Code of Conduct

All contributors and participants in the ScrobbleScope project are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please ensure you are familiar with its terms.

## Questions?

If you have any questions about contributing, feel free to open an issue and tag it with "question".

Thank you for your interest in ScrobbleScope!
