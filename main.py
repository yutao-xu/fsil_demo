import os
import requests
import html2text
from openai import OpenAI
from sec_edgar_downloader import Downloader
from flask import Flask, render_template, request


app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/data/", methods = ['POST', 'GET'])
def data():
    # Ticker is retrived from input box
    ticker = request.form['Ticker']
    sec(ticker)
    return render_template("data.html", item=gpt())

def sec(ticker):
    # Creates an instance of the sec edgar downloader
    dl = Downloader('N/A', 'N/A')

    # Downloads 10-K within the date ranges
    dl.get('10-K', ticker, after='1995-01-01', before='2023-12-31')
    texts = []
    i = 0
    
    # Identifies the directory the 10-Ks are stored in
    directory = 'sec-edgar-filings/' + ticker + '/10-K/'

    # Removes the individual folders and move them to the main folder
    # renames the files starting from 0
    for folder in os.listdir(directory):
        f = os.path.join(directory, folder)
        for file in os.listdir(f):
            j = os.path.join(f, file)
            os.replace(j, directory + str(i))
            i += 1
            os.rmdir(f)
    
    # extracts the first 3000 characters from each file
    for file in os.listdir(directory):
        f = open(os.path.join(directory, file))
        content = html2text.html2text(f.read())
        texts.append(content[:3800])

    # Save in file
    f = open("writeto.txt", "a")
    for i in range(len(texts)):
        f.write(texts[i])
    f.close

def gpt():
    # Open file to analyze
    f = open("writeto.txt", "r")
    contents = f.read()

    # Creates an instance of the LLM
    # Generate insights from prompt
    client = OpenAI()
    completion = client.chat.completions.create(
      model = "gpt-4-turbo",
      messages = [
        {"role": "system", "content": contents},
        {"role": "user", "content": "generate insights"}
      ]
    )

    # Generate an image from insights
    response = client.images.generate(
    model="dall-e-3",
    prompt="generate an image of " + completion.choices[0].message.content,
    size="1024x1024",
    quality="standard",
    n=1,
    ) 

    url = response.data[0].url

    # Save image
    data = requests.get(url).content
    f = open('static/img.jpg', 'wb')
    f.write(data)
    f.close()

    return completion.choices[0].message.content