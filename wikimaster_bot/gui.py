"""Application desktop (PySide6) pour piloter le bot d'ouverture de paquets.

Lancement : python -m wikimaster_bot.gui
"""

import sys

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import browser, storage
from .config import STRATEGIES, load_config, save_config
from .scheduler import scheduler


class ManualLoginWorker(QThread):
    """Ouvre une fenetre de navigateur separee pour la connexion manuelle et
    tourne jusqu'a ce que l'utilisateur la ferme lui-meme."""

    finished_ok = Signal()
    failed = Signal(str)

    def run(self) -> None:
        try:
            browser.open_profile_for_manual_login()
            self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001 - remonte a l'UI
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WikiMasters — Pack Bot")
        self.setMinimumWidth(480)

        self.cfg = load_config()
        self._login_worker: ManualLoginWorker | None = None

        root = QWidget()
        layout = QVBoxLayout(root)
        self.setCentralWidget(root)

        layout.addWidget(self._build_warning_banner())
        layout.addWidget(self._build_status_box())
        layout.addWidget(self._build_settings_box())
        layout.addWidget(self._build_activity_box())

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(1000)
        self.refresh_status()

    # -- construction de l'UI -------------------------------------------------

    def _build_warning_banner(self) -> QLabel:
        label = QLabel(
            "Usage sur compte de test uniquement. L'automatisation d'un jeu peut "
            "violer ses CGU et entrainer un bannissement du compte."
        )
        label.setWordWrap(True)
        label.setStyleSheet("background:#fff8e1; border:1px solid #f0c419; padding:8px; border-radius:6px;")
        return label

    def _build_status_box(self) -> QGroupBox:
        box = QGroupBox("Statut")
        row = QHBoxLayout(box)

        self.bot_status_label = QLabel()
        row.addWidget(self.bot_status_label)
        row.addStretch()

        self.login_button = QPushButton("Se connecter (ouvrir le navigateur)")
        self.login_button.clicked.connect(self.on_login_clicked)
        row.addWidget(self.login_button)

        self.start_button = QPushButton("Demarrer")
        self.start_button.clicked.connect(self.on_start_clicked)
        row.addWidget(self.start_button)

        self.stop_button = QPushButton("Arreter")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        row.addWidget(self.stop_button)

        return box

    def _build_settings_box(self) -> QGroupBox:
        box = QGroupBox("Reglages")
        form = QFormLayout(box)

        self.premium_checkbox = QCheckBox("Compte premium (drop toutes les 3 min au lieu de 10)")
        self.premium_checkbox.setChecked(self.cfg.premium)
        form.addRow(self.premium_checkbox)

        self.max_stock_spin = QSpinBox()
        self.max_stock_spin.setRange(1, 50)
        self.max_stock_spin.setValue(self.cfg.max_stock)
        form.addRow("Stock maximum de paquets", self.max_stock_spin)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(STRATEGIES)
        self.strategy_combo.setCurrentText(self.cfg.strategy)
        self.strategy_combo.currentTextChanged.connect(self._update_interval_enabled)
        form.addRow("Strategie d'ouverture", self.strategy_combo)

        strategy_hint = QLabel(
            "immediate = ouvre des qu'un paquet est disponible\n"
            "batch_at_cap = attend le stock plein puis ouvre tout\n"
            "interval = ouvre a un rythme fixe choisi ci-dessous\n"
            "manual = n'ouvre rien automatiquement"
        )
        strategy_hint.setStyleSheet("color:#666; font-size:11px;")
        form.addRow(strategy_hint)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.5, 240.0)
        self.interval_spin.setSingleStep(0.5)
        self.interval_spin.setValue(self.cfg.interval_minutes)
        form.addRow("Intervalle personnalise (min)", self.interval_spin)
        self._update_interval_enabled(self.cfg.strategy)

        self.headless_checkbox = QCheckBox("Navigateur invisible (headless)")
        self.headless_checkbox.setChecked(self.cfg.headless)
        form.addRow(self.headless_checkbox)

        save_button = QPushButton("Enregistrer les reglages")
        save_button.clicked.connect(self.on_save_settings)
        form.addRow(save_button)

        return box

    def _build_activity_box(self) -> QGroupBox:
        box = QGroupBox("Activite")
        layout = QVBoxLayout(box)

        self.packs_opened_label = QLabel()
        layout.addWidget(self.packs_opened_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        layout.addWidget(self.log_view)

        return box

    def _update_interval_enabled(self, strategy: str) -> None:
        self.interval_spin.setEnabled(strategy == "interval")

    # -- actions ---------------------------------------------------------------

    def on_save_settings(self) -> None:
        self.cfg.premium = self.premium_checkbox.isChecked()
        self.cfg.max_stock = self.max_stock_spin.value()
        self.cfg.strategy = self.strategy_combo.currentText()
        self.cfg.interval_minutes = self.interval_spin.value()
        self.cfg.headless = self.headless_checkbox.isChecked()
        save_config(self.cfg)
        storage.append_log("Reglages mis a jour.")

    def on_start_clicked(self) -> None:
        if self._login_worker is not None and self._login_worker.isRunning():
            QMessageBox.warning(
                self, "Connexion en cours",
                "Ferme d'abord la fenetre de connexion avant de demarrer le bot.",
            )
            return
        self.on_save_settings()
        self.cfg.bot_enabled = True
        save_config(self.cfg)
        scheduler.start(self.cfg)

    def on_stop_clicked(self) -> None:
        self.cfg.bot_enabled = False
        save_config(self.cfg)
        scheduler.stop()

    def on_login_clicked(self) -> None:
        if scheduler.running:
            QMessageBox.warning(
                self, "Bot en cours",
                "Arrete d'abord le bot avant d'ouvrir une fenetre de connexion.",
            )
            return
        self.login_button.setEnabled(False)
        self.login_button.setText("Fenetre ouverte — connecte-toi puis ferme-la")
        storage.append_log("Ouverture du navigateur pour connexion manuelle...")

        worker = ManualLoginWorker(self)
        self._login_worker = worker
        worker.finished_ok.connect(self._on_login_finished)
        worker.failed.connect(self._on_login_failed)
        worker.start()

    def _on_login_finished(self) -> None:
        storage.append_log("Fenetre de connexion fermee.")
        self.login_button.setEnabled(True)
        self.login_button.setText("Se connecter (ouvrir le navigateur)")

    def _on_login_failed(self, message: str) -> None:
        storage.append_log(f"Erreur pendant la connexion manuelle: {message}")
        QMessageBox.critical(self, "Erreur", message)
        self.login_button.setEnabled(True)
        self.login_button.setText("Se connecter (ouvrir le navigateur)")

    # -- rafraichissement --------------------------------------------------------

    def refresh_status(self) -> None:
        running = scheduler.running
        login_running = self._login_worker is not None and self._login_worker.isRunning()
        self.bot_status_label.setText("Bot : en cours" if running else "Bot : arrete")
        self.start_button.setEnabled(not running and not login_running)
        self.stop_button.setEnabled(running)
        self.login_button.setEnabled(not running and not login_running)

        self.packs_opened_label.setText(f"Paquets ouverts : {storage.count_packs_opened()}")
        self.log_view.setPlainText("\n".join(reversed(storage.get_recent_logs(limit=200))))


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
