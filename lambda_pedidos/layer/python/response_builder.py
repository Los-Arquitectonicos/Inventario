"""
Constructor de respuestas HTTP para API Gateway
"""
import json
from datetime import datetime
from bson import ObjectId


class DateTimeEncoder(json.JSONEncoder):
    """Encoder personalizado para datetime y ObjectId"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


def success_response(data, status_code=200):
    """Respuesta exitosa"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False)
    }


def error_response(message, status_code=400):
    """Respuesta de error"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "error": message
        }, ensure_ascii=False)
    }


def not_found_response(resource="Recurso"):
    """Respuesta 404"""
    return error_response(f"{resource} no encontrado", 404)


def validation_error_response(message):
    """Respuesta de validación"""
    return error_response(message, 400)


def server_error_response(message="Error interno del servidor"):
    """Respuesta 500"""
    return error_response(message, 500)
