### You can find all examples in the `/docs/examples/` folder <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/tree/main/docs/examples">here</a>.

These examples use a `.env` file to store keys.
To use the `.env` file you need to install the Python <a target="_blank" href="https://pypi.org/project/python-dotenv/">python-dotenv</a> package.

```python
# INCLUDE THIS FILE IN YOUR .gitignore TO AVOID LEAKING YOUR CREDENTIALS IF YOU ARE PUSHING TO GITHUB!
# learn about gitignore https://git-scm.com/docs/gitignore

app_key = "Your app key"
app_secret = "Your app secret"
callback_url = "https://127.0.0.1"
```