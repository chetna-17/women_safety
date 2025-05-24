from flask import Flask, request, jsonify

app = Flask(__name__, static_url_path='', static_folder='static')

@app.route('/')
def index():
    return app.send_static_file('panic_form.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    print("Received:", data)
    # Process & save data, run predictions, etc.
    return jsonify({"status": "success", "message": "Alert received!"})

if __name__ == "__main__":
    app.run()
