# SPDX-FileCopyrightText: 2024-present Sunil Thaha <sthaha@redhat.com>
#
# SPDX-License-Identifier: MIT
import logging
import sys
import json
import socket
import os
import signal
from datetime import UTC, datetime, timedelta

import click
import pandas as pd

from power_model import trainer
from power_model.__about__ import __version__

logger = logging.getLogger(__name__)


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="power-model")
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["debug", "info", "warn", "error"]),
    default="info",
    required=False,
)
def proxy(log_level: str):
    level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.debug("Log level set to %s", log_level)


def signal_handler(signum):
    click.secho(f"Gracefully shutting down after receiving signal {signum}")
    sys.exit(0)

SERVE_SOCKET = "/tmp/estimator.sock"

class PowerRequest:
    def __init__(self, metrics, values, output_type, source, system_features, system_values, trainer_name="", filter=""):
        self.trainer_name = trainer_name
        self.metrics = metrics
        self.filter = filter
        self.output_type = output_type
        self.energy_source = source
        self.system_features = system_features
        self.datapoint = pd.DataFrame(values, columns=metrics)
        data_point_size = len(self.datapoint)
        for i in range(len(system_features)):
            self.datapoint[system_features[i]] = [system_values[i]] * data_point_size

class Server:
    def __init__(self, socket_path: str, predictor: trainer.Predictor):
        self.socket_path = socket_path
        self.predictor = predictor

    def listen(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self.socket_path)
        s.listen(1)

        logger.info(f"listening on {self.socket_path}")
        while True:
            connection, _ = s.accept()
            self.handle(connection)

    def handle(self, connection):
        data = b""
        while True:
            shunk = connection.recv(1024).strip()
            data += shunk
            if shunk is None or shunk.decode()[-1] == "}":
                break
        decoded_data = data.decode()

        #logger.info(f"request: {decoded_data}")
        try:
            # power_request = json.loads(decoded_data, object_hook=lambda d: PowerRequest(**d))
            j = json.loads(decoded_data)

        except Exception as e:
            msg = f"failed to handle request: {e}"
            logger.error(msg)
            return {"powers": {}, "msg": msg}

        df = pd.DataFrame(j["values"], columns=j["metrics"])
        bpf_cpu_time_ms = df["bpf_cpu_time_ms"].values[0]

        y = self.predictor.kepler_predict(bpf_cpu_time_ms, 0)
        response = json.dumps({"powers": y._asdict(), "msg": "", "core_ratio": 1})
        logger.info(f"response: {bpf_cpu_time_ms}: {response}")
        connection.send(response.encode())


def clean_socket():
    logger.debug("clean socket")
    try:
        os.unlink(SERVE_SOCKET)
    except FileNotFoundError:
        pass


def sig_handler(*args) -> None:
    clean_socket()
    sys.exit(0)

@proxy.command()
@click.option(
    "-f",
    "--file",
    required=True,
    help="Path to the pipeline YAML file.",
    type=click.Path(exists=True),
)
def run(file):
    """Run models based on the provided pipeline configuration and compare the prediction against learning."""

    clean_socket()
    signal.signal(signal.SIGTERM, sig_handler)

    pipeline = trainer.load_pipeline(file)
    predictor = trainer.Predictor(pipeline)

    server = Server(SERVE_SOCKET, predictor)
    try:
        server.listen()
    finally:
        clean_socket()



if __name__ == "__main__":
    proxy()
