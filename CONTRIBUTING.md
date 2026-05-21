# Contributing to SoloCRM

Welcome contributions! We're building a better CRM for solo salespeople, and help is always welcome.

## Code of Conduct

Be respectful, constructive, and kind. Let's build something great together.

## How to Contribute

### 1. Found a Bug?

- Check if it's already reported in [Issues](../../issues)
- If not, open a new issue, please include:
  - What happened
  - What you expected to happen
  - How to reproduce it
  - Your environment (OS, browser, etc.)

### 2. Want to Add a Feature?

- Open an issue first to discuss the feature
- Let's align on whether it fits the project goals before you start coding
- Remember: SoloCRM is designed to be **simple**, we only add features that fit the core 8-use-case design

### 3. Submitting a Pull Request

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### 4. Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/andyrenxu7255/solocrm.git
cd solocrm

# 2. Copy env
cp .env.example .env
# edit .env with your API keys

# 3. Start development with Docker
docker-compose up --build

# 4. Backend local development (optional)
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload

# 5. Frontend local development (optional)
cd frontend
npm install
npm run dev
```

## Coding Guidelines

- Follow the existing directory structure
- Keep it simple, don't over-engineer
- One feature per pull request
- Write clear commit messages
- Make sure your code passes any basic linting

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
