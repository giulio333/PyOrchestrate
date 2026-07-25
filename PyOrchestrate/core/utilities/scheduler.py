import sched
import time
import datetime
from logging import Logger


class Scheduler:
    """
    Gestisce la schedulazione di funzioni in modo flessibile, permettendo l'esecuzione
    a un orario specifico, dopo un certo ritardo o a intervalli regolari.

    Attributi di Classe:
        _scheduler (sched.scheduler): Lo scheduler condiviso tra tutte le istanze della classe.

    Metodi:
        __init__: Inizializza una nuova istanza di Schedulazione con una funzione da eseguire.
        calcola_ritardo_iniziale: Calcola il ritardo iniziale prima della prima esecuzione.
        start: Avvia la schedulazione della funzione.
        _pianifica_prossima_esecuzione: Pianifica la prossima esecuzione della funzione.
        _esegui_funzione: Esegue la funzione e ripianifica la prossima esecuzione se necessario.
        run: Avvia lo scheduler globale per gestire gli eventi pianificati.
        cancel: Cancella l'evento schedulato.
    """

    # Attributo di classe per lo scheduler condiviso
    _scheduler = None

    def __init__(
        self,
        funzione,
        logger,
        args=(),
        kwargs={},
        start_time=None,
        delay=0,
        interval=None,
    ) -> None:
        """
        Inizializza una nuova schedulazione.

        Args:
            funzione (callable): La funzione da eseguire quando l'evento è attivato.
            logger (Logger): Oggetto logger per la registrazione degli eventi.
            args (tuple): Argomenti posizionali da passare alla funzione (opzionale).
            kwargs (dict): Argomenti keyword da passare alla funzione (opzionale).
            start_time (str | datetime.time | datetime.datetime, opzionale): L'orario specifico per la prima esecuzione.
                Può essere una stringa nel formato 'HH:MM:SS' o 'YYYY-MM-DD HH:MM:SS'.
            delay (int, opzionale): Ritardo in secondi prima della prima esecuzione. Se `start_time` è specificato, `delay` è ignorato.
            interval (int, opzionale): Intervallo in secondi per eseguire periodicamente la funzione.

        Raises:
            ValueError: Se `start_time` è nel passato o se non è un formato valido.
        """

        if not Scheduler._scheduler:
            Scheduler._scheduler = sched.scheduler(time.time, time.sleep)

        self.funzione = funzione
        self.args = args
        self.kwargs = kwargs
        self.delay = delay
        self.interval = interval  # Intervallo per esecuzioni periodiche
        self.event = None  # Evento schedulato
        self.logger: Logger = logger

        # Gestione di start_time
        if start_time:
            if isinstance(start_time, str):
                # Prova a convertire la stringa in datetime.time o datetime.datetime
                try:
                    # Prova a interpretare come 'YYYY-MM-DD HH:MM:SS'
                    self.start_time = datetime.datetime.strptime(
                        start_time, "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    try:
                        # Prova a interpretare come 'HH:MM:SS'
                        time_obj = datetime.datetime.strptime(
                            start_time, "%H:%M:%S"
                        ).time()
                        self.start_time = time_obj
                    except ValueError:
                        raise ValueError(
                            "start_time deve essere nel formato 'HH:MM:SS' o 'YYYY-MM-DD HH:MM:SS'"
                        )
            elif isinstance(start_time, (datetime.time, datetime.datetime)):
                self.start_time = start_time
            else:
                raise ValueError(
                    "start_time deve essere una stringa, datetime.time o datetime.datetime"
                )
        else:
            self.start_time = None

        # Pianifica la prima esecuzione
        self.start()

    def calcola_ritardo_iniziale(self):
        """
        Calcola il ritardo iniziale prima della prima esecuzione della funzione.

        Returns:
            float: Il ritardo in secondi prima della prima esecuzione.

        Raises:
            ValueError: Se `start_time` è un oggetto `datetime.datetime` nel passato.
        """

        if self.start_time:
            now = datetime.datetime.now()
            if isinstance(self.start_time, datetime.time):
                scheduled_time = datetime.datetime.combine(now.date(), self.start_time)
                if scheduled_time < now:
                    scheduled_time += datetime.timedelta(days=1)
            elif isinstance(self.start_time, datetime.datetime):
                scheduled_time = self.start_time
                if scheduled_time < now:
                    raise ValueError(f"start_time={scheduled_time} è nel passato.")
            else:
                raise ValueError(
                    "start_time deve essere datetime.time o datetime.datetime"
                )

            delay = (scheduled_time - now).total_seconds()
            return max(0, delay)
        else:
            # Se non è specificato start_time, utilizza il ritardo fornito
            return self.delay

    def start(self):
        """
        Inizia la schedulazione della funzione, calcolando il ritardo iniziale
        e pianificando la prima esecuzione.
        """
        ritardo_iniziale = self.calcola_ritardo_iniziale()
        self._pianifica_prossima_esecuzione(ritardo_iniziale)

    def _pianifica_prossima_esecuzione(self, delay):
        """
        Pianifica la prossima esecuzione della funzione.

        Args:
            delay (float): Ritardo in secondi prima della prossima esecuzione.
        """
        if Scheduler._scheduler:
            self.event = Scheduler._scheduler.enter(delay, 1, self._esegui_funzione)

    def _esegui_funzione(self):
        """
        Esegue la funzione e, se specificato, pianifica la prossima esecuzione
        dopo l'intervallo stabilito.
        """

        self.logger.info(f"executing scheduler job=[{self.funzione.__name__}]")

        self.funzione(*self.args, **self.kwargs)

        if self.interval:
            self._pianifica_prossima_esecuzione(self.interval)

    @classmethod
    def run(cls, blocking=True):
        """
        Esegue lo scheduler globale per gestire gli eventi pianificati.

        Args:
            blocking (bool): Se True, lo scheduler blocca l'esecuzione fino a che non ci sono più eventi pianificati.
        """
        if cls._scheduler:
            cls._scheduler.run(blocking=blocking)

    def cancel(self):
        """
        Cancella l'evento schedulato.

        Se l'evento è già stato eseguito o cancellato, gestisce l'errore in modo sicuro.
        """
        if self.event:
            try:
                if Scheduler._scheduler:
                    Scheduler._scheduler.cancel(self.event)
                    self.logger.debug("Schedulazione cancellata.")
                else:
                    self.logger.debug("Impossibile cancellare l'evento.")
            except ValueError:
                self.logger.debug("L'evento è già stato eseguito o cancellato.")
            self.event = None


if __name__ == "__main__":

    logger = Logger("Scheduler")

    def saluta1(nome):
        print(
            f"{nome} saluta dopo 5 secondi dall'avvio e va via ({datetime.datetime.now().strftime('%H:%M:%S')})"
        )

    def saluta2(nome):
        print(
            f"{nome} saluta alle 21:53:00 e ripete ogni 10 secondi ({datetime.datetime.now().strftime('%H:%M:%S')})"
        )

    def saluta3(nome):
        print(
            f"{nome} saluta ogni 10 secondi ({datetime.datetime.now().strftime('%H:%M:%S')})"
        )

    sched1 = Scheduler(funzione=saluta1, args=("Mario",), delay=5, logger=logger)

    sched2 = Scheduler(
        funzione=saluta2,
        args=("Luisa",),
        start_time="18:53:00",
        interval=10,
        logger=logger,
    )

    sched3 = Scheduler(funzione=saluta3, args=("Luca",), interval=10, logger=logger)

    sched4 = Scheduler(
        funzione=saluta1,
        args=("Giulia",),
        start_time="2025-10-17 18:55:00",
        logger=logger,
    )

    try:

        print("Avvio dello scheduler...")
        Scheduler.run(blocking=True)

    except KeyboardInterrupt:
        print("Esecuzione interrotta dall'utente.")
