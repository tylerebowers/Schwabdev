"""
This is an example of an injected callback capture server for Schwabdev's authentication process (no copy/pasting URLs during auth).
You must have a free port in your callback URL such as `https://127.0.0.1:7777`.
The browser will say that the connection is not secure (e.g. net::ERR_CERT_AUTHORITY_INVALID) because it is using a self-signed certificate, though this is fine because it is a local connection.
"""

import os
import ssl
import http.server
import datetime
import schwabdev
import dotenv
import logging
import webbrowser

def _generate_certificate(common_name="common_name", key_filepath="localhost.key", cert_filepath="localhost.crt"):
        """
        Generate a self-signed certificate for use in capturing the callback during authentication

        Args:
            common_name (str, optional): Common name for the certificate. Defaults to "common_name".
            key_filepath (str, optional): Filepath for the key file. Defaults to "localhost.key".
            cert_filepath (str, optional): Filepath for the certificate file. Defaults to "localhost.crt".

        Notes:
            Schwabdev will change the filepaths to ~/.schwabdev/* (user's home directory)

        """
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        # make folders for cert files
        os.makedirs(os.path.dirname(key_filepath), exist_ok=True)
        os.makedirs(os.path.dirname(cert_filepath), exist_ok=True)

        # create a key pair
        key = rsa.generate_private_key(public_exponent=65537,key_size=2048)

        # create a self-signed cert
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Schwabdev"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Authentication"),
        ]))
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]))
        builder = builder.not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        builder = builder.not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.public_key(key.public_key())
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(common_name)]),
            critical=False,
        )
        builder = builder.sign(key, hashes.SHA256())
        with open(key_filepath, "wb") as f:
            f.write(key.private_bytes(encoding=serialization.Encoding.PEM,
                                      format=serialization.PrivateFormat.TraditionalOpenSSL,
                                      encryption_algorithm=serialization.NoEncryption()))
        with open(cert_filepath, "wb") as f:
            f.write(builder.public_bytes(serialization.Encoding.PEM))
        print(f"Certificate generated and saved to {key_filepath} and {cert_filepath}")

def _launch_capture_server(url_base, url_port):

    # class used to share code outside the http server
    class SharedCode:
        def __init__(self):
            self.code = ""

    # custom HTTP handler to silence logger and get code
    class HTTPHandler(http.server.BaseHTTPRequestHandler):
        shared = None

        def log_message(self, format, *args):
            pass  # silence logger

        def do_GET(self):
            if self.path.find("code=") != -1:
                self.shared.code = f"{self.path[self.path.index('code=') + 5:self.path.index('%40')]}@"
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(b"You may now close this page.")

    shared = SharedCode()

    HTTPHandler.shared = shared
    httpd = http.server.HTTPServer((url_base, url_port), HTTPHandler)
    # httpd.socket.settimeout(1)

    cert_filepath = os.path.expanduser("~/.schwabdev/localhost.crt")
    key_filepath = os.path.expanduser("~/.schwabdev/localhost.key")
    if not (os.path.isfile(cert_filepath) and os.path.isfile(key_filepath)):  # this does not check validity
        _generate_certificate(common_name=url_base, cert_filepath=cert_filepath, key_filepath=key_filepath)

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile=cert_filepath, keyfile=key_filepath)
    # ctx.load_default_certs()

    print(f"[Schwabdev] Listening on port {url_port} for callback...")
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    while len(shared.code) < 1:  # wait for code
        httpd.handle_request()

    httpd.server_close()
    return shared.code

def _custom_auth(auth_url):
    url_split = auth_url.split("://")[-1].split(":")
    url_base = url_split[0]
    url_port = url_split[-1]  # this may or may not have the port

    print(f"Opening browser for authentication at: {auth_url}")
    webbrowser.open(auth_url)  # open the callback url in the browser

    if  not url_port.isdigit():  # if there is a port then capture the callback url
        print("Could not find port in callback url, so you will have to copy/paste the url.")
    else:
        return _launch_capture_server(url_base, int(url_port))


if __name__ == "__main__":
    dotenv.load_dotenv()  # load environment variables from .env file

    logging.basicConfig(level=logging.INFO)

    client = schwabdev.Client(
        os.getenv('app_key'),
        os.getenv('app_secret'),
        os.getenv('callback_url'),
        call_on_auth=_custom_auth
    )

    # manually trigger the auth flow to demonstrate the callback capture
    client.tokens.update_tokens(force_refresh_token=True)  

    print("Modified auth flow complete.")

    print(client.linked_accounts().json())