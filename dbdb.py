from flask import Flask, request, render_template, redirect, url_for, abort
import dbdb

app = Flask(__name__)

@app.route('/form')
def form():
    return render_template('test.html')

@app.route('/method', methods=['GET', 'POST'])
def method():
    if request.method == 'GET':
        return 'GET 으로 전송이다.'
    else:
        num = request.form["num"]
        name = request.form["name"]
        dbdb.insert_data(num, name)
        return 'POST 이다. 학번은: {} 이름은: {}'.format(num, name)

@app.route('/getinfo')
def getinfo():
    info = dbdb.select_all()
    retstr = ''
    for i, v in enumerate(info):
        retstr += '%d. 학번: %s 이름: %s<br>' % (i+1, v[0], v[1])
    return retstr