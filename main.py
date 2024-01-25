from gemini_pro_bot.bot import start_bot

from flask import Flask,render_template
from threading import Thread
import os
"""import streamlit as st

def main():
    st.title("Simple Streamlit App")
    
    # Add some content to your app
    st.write("Welcome to my Streamlit app!")

    # Add a simple input field
    user_input = st.text_input("Enter your name:", "Type here...")

    # Display a greeting
    st.write(f"Hello, {user_input}!")
"""
app = Flask(__name__)
@app.route('/')
def index():
    return "Alive"
def run():
  app.run(host='0.0.0.0',port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    start_bot()
