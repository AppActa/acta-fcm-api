from argparse import ArgumentParser
import logging
from contextlib import contextmanager
from app.database.postgres import get_conn
from app.services.lembretes import executar_lembretes

logger = logging.getLogger(__name__)

def main() -> int:
    ArgumentParser(description='Lembretes de tarefas com prazo para amanhã.').parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    try:
        with contextmanager(get_conn)() as conn:
            totais = executar_lembretes(conn)
    except Exception as erro:
        logger.error('Não foi possível executar lembretes: %s', type(erro).__name__)
        return 1

    logger.info('Lembretes totais=%s', totais)
    return 1 if totais['falhas'] else 0

if __name__ == '__main__':
    raise SystemExit(main())