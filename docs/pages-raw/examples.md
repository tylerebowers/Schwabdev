### You can find all examples in the `/docs/examples/` folder <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/tree/main/docs/examples">here</a>.

These examples use a `.env` file to store keys (make this file in the same folder as your script).
To use the `.env` file you need to install the Python <a target="_blank" href="https://pypi.org/project/python-dotenv/">python-dotenv</a> package.

```python
# INCLUDE THIS FILE IN YOUR .gitignore TO AVOID LEAKING YOUR CREDENTIALS IF YOU ARE PUSHING TO GITHUB!
# learn about gitignore https://git-scm.com/docs/gitignore

app_key = "Your app key"
app_secret = "Your app secret"
callback_url = "https://127.0.0.1"
```

### Main Examples

* api_demo.py - Examples of all api calls that can be made, orders are commented out to avoid accidental trades.
* async_api_calls.py - Example of making asynchronous api calls with `schwabdev.ClientAsync`.
* jupyter_demo.ipynb - Notebook demonstrating usage of Schwabdev in a Jupyter notebook.
* playground.py - A python interactive session to test code snippets, run via `python -i playground.py`
* stream_demo.py - Example of all real-time streamable assets for the streaming client.

### Extra Examples (in /extras/ folder)

* api_gui_demo.py - A simple GUI application demonstrating Schwabdev functionality using Tkinter.
* async_api_demo_parsed.py - An asynchronous example demonstrating parsed data from various endpoints.
* async_playground.py - An interactive asynchronous python session to test code snippets, run via `python -i async_playground.py`
* async_stream_demo.py - An asynchronous example demonstrating real-time streaming data.
* capture_callback.py - A custom auth flow using a web server to capture OAuth2 callback codes.
* charting.py - Graphing streamed data using matplotlib.
* concurrent_stream_calls.py - Demonstrates making concurrent streaming calls using asyncio.
* encrypted_db_setup.py - Example of setting up an encrypted tokens database using the `cryptography` package.
* processing_streaming_data.py - An example of processing streamed data.
* template.py - A template file for all of these examples.
* translating_stream.py - An example of translating level_one_equities streaming data fields into a human-readable format.