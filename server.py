import hashlib
from concurrent import futures
import decimal
from urllib import parse
from urllib.parse import urlparse
import grpc
import payment_pb2, payment_pb2_grpc


def generate_payment_link(
    merchant_login: str,  # Merchant login
    merchant_password_1: str,  # Merchant password
    cost: decimal,  # Cost of goods, RU
    number: int,  # Invoice number
    description: str,  # Description of the purchase
    is_test = 0,
    robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx',
) -> str:
    """URL for redirection of the customer to the service.
    """
    signature = calculate_signature(
        merchant_login,
        cost,
        number,
        merchant_password_1
    )

    data = {
        'MerchantLogin': merchant_login,
        'OutSum': cost,
        'InvId': number,
        'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test
    }
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


def check_signature_result(

    order_number: int,  # invoice number
    received_sum: decimal,  # cost of goods, RU
    received_signature: hex,  # SignatureValue
    password: str  # Merchant password
) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    if signature.lower() == received_signature.lower():
        return True
    return False


def parse_response(request: str) -> dict:
    """
    :param request: Link.
    :return: Dictionary.
    """
    params = {}

    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params

def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()




class PaymentService(payment_pb2_grpc.PaymentServiceServicer):
    def ResultPayment(self, request, context):
        param_request = parse_response(request.request)
        cost = param_request['OutSum']
        number = param_request['InvId']
        signature = param_request['SignatureValue']

        if check_signature_result(number, cost, signature, request.merchant_password_2):
            return payment_pb2.ResultPaymentResponse(result=f'OK{param_request["InvId"]}')

        return payment_pb2.ResultPaymentResponse(result="bad sign")

    def GeneratePaymentLink(self, request, context):
        # Ваша логика обработки метода GeneratePaymentLink
        cost = request.cost
        number = request.number
        description = request.description
        # другие поля запроса
        print(request.merchant_login, request.merchant_password_1, cost, number, description, )
        result = generate_payment_link(request.merchant_login, request.merchant_password_1, cost, number, description, 0)
        return payment_pb2.GeneratePaymentLinkResponse(payment_link=result)


def run_server():
    server = grpc.server(futures.ThreadPoolExecutor())
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    run_server()
