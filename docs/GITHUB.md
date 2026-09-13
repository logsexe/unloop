# Publishing UNLOOP to GitHub

UNLOOP is designed to live as a normal Git repository. Never commit `.env`, OAuth tokens, or `data/unloop.db`.

After creating an empty GitHub repository, from the project root run:

```powershell
.\scripts\bootstrap-github.ps1 -RepositoryUrl "https://github.com/YOUR_USER/unloop.git"
```

The project `.gitignore` excludes local secrets and runtime database data.
