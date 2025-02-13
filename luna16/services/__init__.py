import typing

import mlflow
from torch.utils.tensorboard.writer import SummaryWriter

from .creators import (
    clean_mlflow_experiment,
    clean_tensorboard_writer,
    create_mlflow_experiment,
    create_training_writer,
    create_validation_writer,
)
from .model_saver import BaseModelSaver, MLFlowModelSaver, ModelSaver
from .service_container import (
    ServiceContainer,
)

TrainingWriter = typing.NewType("TrainingWriter", SummaryWriter)
ValidationWriter = typing.NewType("ValidationWriter", SummaryWriter)
MlFlowRun = typing.NewType("MlFlowRun", mlflow.ActiveRun)


__all__ = [
    "BaseModelSaver",
    "MLFlowModelSaver",
    "MlFlowRun",
    "ModelSaver",
    "ServiceContainer",
    "TrainingWriter",
    "ValidationWriter",
    "clean_mlflow_experiment",
    "clean_tensorboard_writer",
    "create_mlflow_experiment",
    "create_training_writer",
    "create_validation_writer",
]
