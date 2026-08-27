from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class RegisterUserSchema(Schema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "username is required"},
    )
    email = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "email is required"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "password is required"},
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf(['buyer', 'seller'], error="user role must be buyer or seller only"),
        error_messages={"required": "role is required"},
    )

    @pre_load
    def strip_fields(self, data, **kwargs):
        if 'username' in data and isinstance(data['username'], str):
            data['username'] = data['username'].strip()
            if not data['username']:
                data['username'] = None
        if 'email' in data and isinstance(data['email'], str):
            data['email'] = data['email'].strip()
            if not data['email']:
                data['email'] = None
        if 'password' in data and isinstance(data['password'], str):
            if not data['password'].strip():
                data['password'] = None
        return data

    @validates('email')
    def validate_email(self, value, **kwargs):
        if value and not EMAIL_REGEX.match(value):
            raise ValidationError("invalid email format")


class LoginSchema(Schema):
    email = fields.String(
        required=True,
        error_messages={"required": "email and password are required"},
    )
    password = fields.String(
        required=True,
        error_messages={"required": "email and password are required"},
    )

    @pre_load
    def check_empty(self, data, **kwargs):
        if 'email' in data and isinstance(data['email'], str):
            if not data['email'].strip():
                data['email'] = None
        if 'password' in data and isinstance(data['password'], str):
            if not data['password'].strip():
                data['password'] = None
        return data


class UserResponseSchema(Schema):
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    role = fields.String()
    last_login = fields.DateTime(format='iso', allow_none=True)
    created_at = fields.DateTime(format='iso')


class UserPublicResponseSchema(Schema):
    username = fields.String()
    email = fields.String()
