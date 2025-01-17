# SPDX-FileCopyrightText: 2024-present Sunil Thaha <sthaha@redhat.com>
#
# SPDX-License-Identifier: MIT
import logging
import sys
import time
from datetime import UTC, datetime, timedelta

import click
from prometheus_client import start_http_server, Gauge

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
def pm(log_level: str):
    level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.debug("Log level set to %s", log_level)


@pm.command()
@click.option(
    "-f",
    "--file",
    required=True,
    help="Path to the pipeline YAML file.",
    type=click.Path(exists=True),
)
def train(file):
    """Train models based on the provided pipeline configuration."""

    try:
        pipeline = trainer.load_pipeline(file)
        trainer.train(pipeline)
        click.echo("Training completed successfully.")

    except Exception as e:
        click.echo(f"An error occurred: {e}")
        # print stack
        import traceback

        traceback.print_exc()

def signal_handler(signum):
    click.secho(f"Gracefully shutting down after receiving signal {signum}")
    sys.exit(0)

@pm.command()
@click.option(
    "-f",
    "--file",
    required=True,
    help="Path to the pipeline YAML file.",
    type=click.Path(exists=True),
)
def run(file):
    """Run models based on the provided pipeline configuration and compare the prediction against learning."""

    # try:
    pipeline = trainer.load_pipeline(file)
    predictor = trainer.Predictor(pipeline)
    target = Gauge('st_power_model_target',
                   'CPU Frequency as reported by turbostat',
                   ["pipeline", "model"])

    try:
        while True:
            preditions = predictor.predict()
            for p in preditions:
                target.labels(p.pipeline, p.model).set(p.y_pred)
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("Exiting...")

    # except Exception as e:
    #    click.echo(f"An error occurred: {e}")


@pm.command()
@click.option(
    "-f",
    "--file",
    required=True,
    help="Path to the pipeline YAML file.",
    type=click.Path(exists=True),
)
@click.option(
    "-s",
    "--start",
    required=False,
    help="Path to the pipeline YAML file.",
    type=click.DateTime(),
    default=None,
)
@click.option(
    "-e",
    "--end",
    required=False,
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%SZ"]),
    default=datetime.now(UTC),
)
@click.option(
    "-d",
    "--duration",
    required=False,
    type=int,
    default=5 * 60,
)
def compute_error(file, start: datetime|None, end: datetime, duration: int):
    """Run models based on the provided pipeline configuration and compare the prediction against learning."""

    if start is None:
        if duration == 0:
            raise click.ClickException("Please provide start or non-zero duration")

        start = end - timedelta(seconds=duration)

    if start is not None and duration > 0:
        end = start + timedelta(seconds=duration)

    pipeline = trainer.load_pipeline(file)
    predictor = trainer.Predictor(pipeline)

    click.secho(f"Predicting from {start} to {end}")
    predictor.predict_range(start, end)


if __name__ == "__main__":
    pm()
