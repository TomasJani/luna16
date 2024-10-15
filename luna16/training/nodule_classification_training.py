import typing
from datetime import datetime
from functools import partial

import torch
from ray import tune
from torch.profiler import ProfilerActivity, profile, schedule

from luna16 import (
    batch_iterators,
    datasets,
    dto,
    hyperparameters_container,
    message_handler,
    models,
    modules,
    trainers,
)
from luna16.settings import settings

if typing.TYPE_CHECKING:
    from luna16 import services


class LunaClassificationLauncher:
    def __init__(
        self,
        training_name: str,
        validation_stride: int,
        num_workers: int,
        registry: "services.ServiceContainer",
        validation_cadence: int,
        training_length: int | None = None,
    ) -> None:
        self.training_name = training_name
        self.validation_stride = validation_stride
        self.validation_cadence = validation_cadence
        self.num_workers = num_workers
        self.training_length = training_length
        self.registry = registry
        self.logger = registry.get_service(message_handler.MessageHandler)
        self.hyperparameters = registry.get_service(
            hyperparameters_container.HyperparameterContainer
        )
        self.batch_iterator = batch_iterators.BatchIteratorProvider(logger=self.logger)

    def fit(
        self,
        *,
        epochs: int,
        batch_size: int,
        lr: float,
        momentum: float,
        conv_channels: int,
        profile: bool,
    ) -> dto.Scores:
        module = modules.LunaModel(
            in_channels=1,
            conv_channels=conv_channels,
        )
        model = models.NoduleClassificationModel(
            model=module,
            optimizer=torch.optim.SGD(module.parameters(), lr=lr, momentum=momentum),
            batch_iterator=self.batch_iterator,
            logger=self.logger,
            validation_cadence=self.validation_cadence,
        )
        trainer = trainers.Trainer[dto.LunaClassificationCandidate](
            name=self.training_name, logger=self.logger
        )
        train, validation = datasets.create_pre_configured_luna_rationed(
            validation_stride=self.validation_stride,
            training_length=self.training_length,
        )
        data_module = datasets.DataModule(
            batch_size=batch_size,
            num_workers=self.num_workers,
            train=train,
            validation=validation,
        )
        if profile:
            tracing_schedule = schedule(
                skip_first=1, wait=1, warmup=1, active=1, repeat=4
            )
            return trainer.fit_profile(
                model=model,
                epochs=epochs,
                data_module=data_module,
                tracing_schedule=tracing_schedule,
            )
        return trainer.fit(model=model, epochs=epochs, data_module=data_module)

    def tune_parameters(
        self,
        epochs: int,
    ) -> tune.ResultGrid:
        hyperparameters: dict[str, typing.Any] = {
            "batch_size": tune.grid_search([16, 32, 64]),
            "learning_rate": tune.grid_search([0.0001, 0.001, 0.01]),
            "momentum": tune.grid_search([0.97, 0.98, 0.99]),
        }
        self.tunable_fit = partial(
            self.fit,
            epochs=epochs,
        )
        tuner = tune.Tuner(self.tunable_fit, param_space=hyperparameters)
        return tuner.fit()

    def profile_model(
        self,
        *,
        lr: float,
        momentum: float,
        conv_channels: int,
        batch_size: int,
    ) -> None:
        self.logger.registry.call_all_creators(
            training_name=self.training_name, training_start_time=datetime.now()
        )
        module = modules.LunaModel(
            in_channels=1,
            conv_channels=conv_channels,
        )
        train, validation = datasets.create_pre_configured_luna_rationed(
            validation_stride=self.validation_stride,
            training_length=self.training_length,
        )
        data_module = datasets.DataModule(
            batch_size=batch_size,
            num_workers=self.num_workers,
            train=train,
            validation=validation,
        )
        model = models.NoduleClassificationModel(
            model=module,
            optimizer=torch.optim.SGD(module.parameters(), lr=lr, momentum=momentum),
            batch_iterator=self.batch_iterator,
            logger=self.logger,
            validation_cadence=self.validation_cadence,
        )
        with profile(
            activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
            # with_stack=True,
            # record_shapes=True,
            # profile_memory=True,
        ) as prof:
            model.do_training(
                epoch=1, train_dataloader=data_module.get_training_dataloader()
            )

        # Chrome trace can be viewed in chrome://tracing
        prof.export_chrome_trace(str(settings.BASE_DIR / "chrome_trace.json"))
        # prof.export_memory_timeline(str(settings.BASE_DIR / "memory_timeline.html"))
        # prof.export_stacks(str(settings.BASE_DIR / "stacks"))
