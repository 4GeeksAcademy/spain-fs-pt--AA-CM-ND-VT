"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, Users, Companies, Bookings, MasterServices, Ratings, Requests, Services
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity,unset_jwt_cookies
from flask_bcrypt import Bcrypt

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)
bcrypt=Bcrypt()

@api.route('/landing', methods=['GET'])
def landing():
    return jsonify({'message': 'Welcome to the landing page!'})

@api.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    new_user = Users(name=data['name'], email=data['email'], 
                     password=data['password'], rol=data['rol'])
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()), 201
    except Exception as ex:
        db.session.rollback()
        return jsonify({'error': 'User with this email already exists', 'error': str(ex)}), 400
    
@api.route('/signup_company', methods=['POST'])
def signup_company():
    data = request.get_json()
    new_user = Users(name=data['name'], email=data['email'], 
                     password=data['password'], rol=data['rol'])
    try:
        db.session.add(new_user)
        db.session.commit()
        new_company = Companies(name=data['company_name'], location=data['location'], owner=new_user.id)
        db.session.add(new_company)
        db.session.commit()
        return jsonify(new_user.serialize()), 201
    except Exception as ex:
        db.session.rollback()
        return jsonify({'error': 'User with this email already exists', 'error': str(ex)}), 400


@api.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"msg": "Logout successful"})
    unset_jwt_cookies(response)
    return response, 200

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Users.query.filter_by(email=data['email']).first()

    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({"msg": "Bad email or password"}), 401

    company = Companies.query.filter_by(user=user).first()

    access_token = create_access_token(identity=user.id)
    
    response = {
        'access_token': access_token,
        'user_id': user.id,
        'username': user.name,
        'rol': user.rol
    }

    if company:
        response['companyname'] = company.name
        response['company_id'] = company.id

    return jsonify(response)

@api.route('/clientportal/<int:user_id>', methods=['GET'])
@jwt_required()
def client_portal(user_id):
    user = Users.query.get_or_404(user_id)
    if user.rol != 'client':
        return jsonify({'error': 'User is not a client'}), 400
    return jsonify(user.serialize())

@api.route('/clientportal/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    data = request.get_json()
    user = Users.query.get_or_404(user_id)
    
    if user.rol != 'client':
        return jsonify({'error': 'User is not a client'}), 400

@api.route('/companyservices/<int:user_id>/service/<int:service_id>', methods=['DELETE'])
def delete_service(user_id, service_id):
    user = Users.query.get_or_404(user_id)
    print(f"user id:{user_id},user role:{user.rol}")
    if user.rol not in["company","admin"]:
        return jsonify({'error': 'Unauthorized access, only companies allowed'}), 403
    service = Services.query.get_or_404(service_id)
    if service.companies_id != user_id:
        return jsonify({'error': 'Unauthorized access to delete this service'}), 403
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Service deleted successfully'}), 200


@api.route('/adminportal/<int:company_id>', methods=['GET'])
@jwt_required()
def company_portal(company_id):
    company = Companies.query.get_or_404(company_id)
    return jsonify([company.serialize()])

@api.route('/adminportal/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_company_admin(company_id):
    current_user_id = get_jwt_identity()
    current_user = Users.query.get(current_user_id)

    # Verificar que el usuario tiene el rol correcto
    if current_user.rol != 'company':
        return jsonify({'error': 'User is not authorized'}), 403

    # Obtener la empresa a actualizar
    company = Companies.query.get_or_404(company_id)
    
    data = request.get_json()
    
    # Actualizar los campos de la empresa
    company.name = data.get('name', company.name)
    company.location = data.get('location', company.location)
    company.owner = data.get('owner', company.owner)
    company.image = data.get('image', company.image)

    try:
        db.session.commit()
        return jsonify(company.serialize()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api.route('/master_services', methods=['GET'])
def get_master_services():
    master_services = MasterServices.query.all()
    return jsonify([service.serialize() for service in master_services]), 200

@api.route('/services', methods=['GET'])
def get_services():
    companies_id = request.args.get('companies_id')
    if companies_id:
        services = Services.query.filter_by(companies_id=companies_id).all()
    else:
        services = Services.query.all()
    return jsonify([service.serialize() for service in services]), 200

@api.route('/all_services', methods=['GET'])
def get_all_services():
    services = Services.query.all()
    return jsonify([service.serialize() for service in services]), 200

@api.route('/services', methods=['POST'])
def add_service():
    data = request.get_json()
    companyid = data.get('companyid')
    new_service = Services(
        name=data['name'],
        description=data['description'],
        type=data['type'],
        price=data['price'],
        duration=data['duration'],
        companies_id=companyid,  # Use the provided user's ID to link the service to their company
        available=data['available'],
        image=data['image']
    )
    db.session.add(new_service)
    db.session.commit()

    return jsonify(new_service.serialize()), 201

@api.route('/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    data = request.get_json()
    userid = data.get('user_id')
    serviceid = data.get('services_id')
    new_booking = Bookings(
        services_id=serviceid,
        users_id=userid,
        start_day_date=data['start_day_date'],
        start_time_date=data['start_time_date']
    )
    db.session.add(new_booking)
    db.session.commit()    
    booking_id = new_booking.id
    
    response_data = new_booking.serialize()
    response_data['id'] = booking_id
    
    return jsonify(response_data), 201

@api.route('/requests', methods=['POST'])
@jwt_required()
def create_request():
    data = request.get_json()
    new_request = Requests(
        bookings_id=data.get('booking_id'),
        status=data.get('status'),
        comment=data.get('comment')
    )
    db.session.add(new_request)
    db.session.commit()
    return jsonify(new_request.serialize()), 201

@api.route('/user_bookings', methods=['GET'])
def get_user_bookings():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"msg": "User ID is required"}), 400
    bookings = Bookings.query.filter_by(users_id=user_id).all()
    return jsonify([booking.serialize() for booking in bookings]), 200

@api.route('/user_requests', methods=['GET'])
def get_user_requests():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"msg": "User ID is required"}), 400
    requests = Requests.query.join(Bookings).filter(Bookings.users_id == user_id).all()
    return jsonify([request.serialize() for request in requests]), 200

@api.route('/company_bookings', methods=['GET'])
def get_company_bookings():
    company_id = request.args.get('company_id')
    if not company_id:
        return jsonify({"msg": "Company ID is required"}), 400
    bookings = Bookings.query.join(Services).filter(Services.companies_id == company_id).all()
    return jsonify([booking.serialize() for booking in bookings]), 200

@api.route('/company_requests', methods=['GET'])
def get_company_requests():
    company_id = request.args.get('company_id')
    if not company_id:
        return jsonify({"msg": "Company ID is required"}), 400
    requests = Requests.query.join(Bookings).join(Services).filter(Services.companies_id == company_id).all()
    return jsonify([request.serialize() for request in requests]), 200

@api.route('/update_request', methods=['POST'])
def update_request():
    data = request.get_json()
    request_id = data.get('requestId')
    status = data.get('status')
    comment = data.get('comment')

    request_to_update = Requests.query.get(request_id)
    if not request_to_update:
        return jsonify({"msg": "Request not found"}), 404

    request_to_update.status = status
    request_to_update.comment = comment
    db.session.commit()
    return jsonify({"msg": "Request updated successfully"}), 200
    