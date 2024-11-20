"""A script to do web-scraping.
Specifically in this case we are accesing a mailing list admin page and
extracting a list of members' email addresses.
"""

import argparse
from getpass import getpass
from cryptography.fernet import Fernet
import os

# Generate a key for encryption
key = Fernet.generate_key()
cipher = Fernet(key)

# Securely get the email and password
email_address = input("Enter the email address: ")
pwd = cipher.encrypt(getpass("Enter your password: ").encode())

print("\nLogging in...")

# example
print(f"Email: {email_address}")
print(f"PWD_encrypted: {pwd}")
print(f"PWD_decrypted: {cipher.decrypt(pwd).decode()}")
