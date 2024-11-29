from src.repository.health_check_repository import get_orion_version

def check_orion_version():
    """
    Serviço responsável por verificar a versão do Orion Context Broker.
    """
    return get_orion_version()
