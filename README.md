# Schwabdev
![PyPI - Version](https://img.shields.io/pypi/v/schwabdev) ![Discord](https://img.shields.io/discord/1076596998150561873?logo=discord) ![PyPI - Downloads](https://img.shields.io/pypi/dm/schwabdev) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?business=8VDFKHMBFSC2Q&no_recurring=0&currency_code=USD) ![YouTube Video Views](https://img.shields.io/youtube/views/kHbom0KIJwc?style=flat&logo=youtube)  
This package is not affiliated with or endorsed by Schwab, it is maintained by [Tyler Bowers](https://github.com/tylerebowers) & [Contributors](https://github.com/tylerebowers/Schwabdev/graphs/contributors).   
Licensed under the MIT license. Acts in accordance with Schwab's API terms and conditions.  
Useful links:
* Join the [Discord](https://discord.gg/m7SSjr9rs9) to ask questions or get help.
* Read the [Documentation](https://tylerebowers.github.io/Schwabdev/).
* View the [PyPI](https://pypi.org/project/schwabdev/) package page.
* Watch the [Youtube](https://youtube.com/playlist?list=PLs4JLWxBQIxpbvCj__DjAc0RRTlBz-TR8) tutorials.
* View the [Github](https://github.com/tylerebowers/Schwab-API-Python) repository.

### Quick Start Guide: [Start Here](https://tylerebowers.github.io/Schwabdev/?source=pages%2Fquickstart.html)


### What can this program do?
- Automatic token management and refreshes.  
- Authenticate and access the full api with minimal code. [see examples](https://github.com/tylerebowers/Schwabdev/tree/main/docs/examples/api_demo.py)  
- Stream real-time data with a customizable response handler [see examples](https://github.com/tylerebowers/Schwabdev/tree/main/docs/examples/stream_demo.py)  
- Place orders and get order details [see examples](https://tylerebowers.github.io/Schwabdev/?source=pages%2Forders.html)  
- Optional capture of callback urls when callback has a port (starts webserver on this port).  
- Optional automatic starting/stopping of streamer when market opens/closes.  
- Streaming stability with automatic restarts if the streamer crashes.  

### Developer Notes
The schwabdev folder contains code for main operations:   
 - `__init__.py` linker to client class.
 - `client.py` contains functions relating to api calls and requests.
 - `tokens.py` contains functions relating to token management.
 - `stream.py` contains functions for streaming data from websockets.

### Youtube Tutorials
*Github code has changed since these videos*
1. [Authentication and Requests](https://www.youtube.com/watch?v=kHbom0KIJwc&ab_channel=TylerBowers) 
2. [Streaming Real-time Data](https://www.youtube.com/watch?v=t7F2dUecgWc&list=PLs4JLWxBQIxpbvCj__DjAc0RRTlBz-TR8&index=2&ab_channel=TylerBowers) 

### MIT License

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
