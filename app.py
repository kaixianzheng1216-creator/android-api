import datetime
import random

from flask import Flask, request, jsonify, send_from_directory
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from waitress import serve
from werkzeug.security import generate_password_hash, check_password_hash
from paste.translogger import TransLogger

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/android_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = '2722940234@qq.com'
app.config['MAIL_PASSWORD'] = 'rzcbslafadbidehf'
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80))
    bio = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "bio": self.bio
        }


class EmailCode(db.Model):
    __tablename__ = 'email_codes'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)


class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255))
    detail = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "address": self.address,
            "detail": self.detail,
        }


def check_code(email, code):
    limit = datetime.datetime.now() - datetime.timedelta(minutes=5)

    return EmailCode.query.filter(
        EmailCode.email == email,
        EmailCode.code == code,
        EmailCode.created_at > limit
    ).first()


@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"code": 400, "msg": "请输入邮箱"}), 400

    code = str(random.randint(100000, 999999))
    db.session.add(EmailCode(email=email, code=code))
    db.session.commit()

    mail.send(Message("注册验证码", recipients=[email], body=f"验证码：{code}"))

    return jsonify({"code": 200, "msg": "发送成功"})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json

    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    code = data.get('code')

    if not all([email, password, username, code]):
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    if not check_code(email, code):
        return jsonify({"code": 400, "msg": "验证码错误或过期"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"code": 400, "msg": "邮箱已存在"}), 400

    user = User(
        email=email,
        password=generate_password_hash(password),
        username=username
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"code": 200, "msg": "注册成功", "data": user.to_dict()})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"code": 400, "msg": "请输入账号密码"}), 400

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        return jsonify({"code": 200, "msg": "登录成功", "data": user.to_dict()})

    return jsonify({"code": 401, "msg": "账号或密码错误"}), 401


@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')

    if not all([email, code, new_password]):
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    if not check_code(email, code):
        return jsonify({"code": 400, "msg": "验证码错误"}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        user.password = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({"code": 200, "msg": "重置成功"})

    return jsonify({"code": 404, "msg": "用户不存在"}), 404


@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    bio = data.get('bio')

    if not email:
        return jsonify({"code": 400, "msg": "邮箱参数缺失"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    if username:
        user.username = username

    if bio is not None:
        user.bio = bio

    db.session.commit()

    return jsonify({"code": 200, "msg": "更新成功", "data": user.to_dict()})


@app.route('/api/user_info', methods=['POST'])
def get_user_info():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"code": 400, "msg": "邮箱参数缺失"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    user_data = user.to_dict()
    user_data['course_count'] = 12
    user_data['study_time'] = "45h"
    user_data['certificate_count'] = 3

    return jsonify({"code": 200, "msg": "获取成功", "data": user_data})


@app.route('/api/addresses', methods=['GET'])
def get_addresses():
    email = request.args.get('email')
    if not email:
        return jsonify({"code": 400, "msg": "参数缺失"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    addresses = Address.query.filter_by(user_id=user.id).all()
    return jsonify({"code": 200, "msg": "获取成功", "data": [addr.to_dict() for addr in addresses]})


@app.route('/api/addresses', methods=['POST'])
def add_address():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    phone = data.get('phone')
    detail = data.get('detail')
    address_val = data.get('address', '')

    if not all([email, name, phone, address_val]):
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"code": 404, "msg": "用户不存在"}), 404

    address = Address(
        user_id=user.id,
        name=name,
        phone=phone,
        address=address_val,
        detail=detail,
    )
    db.session.add(address)
    db.session.commit()

    return jsonify({"code": 200, "msg": "添加成功", "data": address.to_dict()})


@app.route('/api/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    detail = data.get('detail')
    address_val = data.get('address')

    if not all([name, phone, detail, address_val]):
        return jsonify({"code": 400, "msg": "参数不完整"}), 400

    address = Address.query.get(address_id)
    if not address:
        return jsonify({"code": 404, "msg": "地址不存在"}), 404

    address.name = name
    address.phone = phone
    address.detail = detail
    address.address = address_val

    db.session.commit()

    return jsonify({"code": 200, "msg": "更新成功", "data": address.to_dict()})


@app.route('/api/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    address = Address.query.get(address_id)
    if not address:
        return jsonify({"code": 404, "msg": "地址不存在"}), 404

    db.session.delete(address)
    db.session.commit()

    return jsonify({"code": 200, "msg": "删除成功"})


@app.route('/api/home_ad_list_data.json')
def home_ad_list_data():
    return send_from_directory('data', 'home_ad_list_data.json')


@app.route('/api/home_news_list_data.json')
def home_news_list_data():
    return send_from_directory('data', 'home_news_list_data.json')


@app.route('/api/course_list_data.json')
def course_list_data():
    return send_from_directory('data', 'course_list_data.json')


@app.route('/api/algorithm_list_data.json')
def algorithm_list_data():
    return send_from_directory('data', 'algorithm_list_data.json')


@app.route('/api/tech_column_list_data.json')
def tech_column_list_data():
    return send_from_directory('data', 'tech_column_list_data.json')


@app.route('/api/open_source_list_data.json')
def open_source_list_data():
    return send_from_directory('data', 'open_source_list_data.json')


@app.route('/api/video_list_data.json')
def video_list_data():
    return send_from_directory('data', 'video_list_data.json')


@app.route('/api/img/<path:filename>')
def serve_images(filename):
    return send_from_directory('data/img', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    logged_app = TransLogger(app, setup_console_handler=True)

    serve(logged_app, host='0.0.0.0', port=5000, threads=10)