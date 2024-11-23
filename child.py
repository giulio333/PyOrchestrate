from base import BaseProcess, TConfig


class ChildProcess(BaseProcess[TConfig]):
    """
    Classe base ChildProcess.

    Il metodo `work` deve essere implementato nelle sottoclassi per definire il lavoro da svolgere.

    Attributes:
    name (str): Nome del processo.
    config (TConfig): Configurazioni del processo.
    logger (Logger): Logger del processo.
    """

    def __init__(self, name: str, config: TConfig):
        super().__init__(name, config)
