from flask import Flask
from floorplanGAN import FloorplanGAN
import json
import request

app = Flask(__name__)


@app.route('//algorithm/design', methods=['POST'])
def design():
    data = json.loads(request.get_data(as_text=True))
    result = {}
    try:
        num = data['nodes_num']
        room_type = data['type']
        edges = data['edges']
        floorplanGAN = FloorplanGAN(num, room_type, edges)
        floorplanGAN.design()
        result[''] = 400
        result[''] = 'http://localhost:8081/result.png'
    except KeyError:
        result['code'] = 400
        result['error'] = '缺少参数'
    return result


if __name__ == '__main__':
    app.run()
